"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.SSHResourceManager
==================================

APIs
----
"""
import json
import logging
import os
import sys

import paramiko as pm

from .CPUResourceManager import CPUResourceManager
from ...utils import check_missing_key, load_default_env, parse_result, DEFAULT_AUPTIMIZER_PATH

logger = logging.getLogger(__name__)
# logging.getLogger("paramiko").setLevel(logger.getEffectiveLevel())
logging.getLogger("paramiko").setLevel(logging.CRITICAL)


def parse_hostname(host):
    """
    Parse the host name, in the following formats:

    + `username@ip` or
    + `username@ip:port` or
    + `username@ip ssh_key` or
    + `username@ip:port ssh_key`

    :param host: host name string
    :type host: str
    :return: username, hostname, port=22, key (parsed from ~/.ssh/id_rsa)
    """
    if "@" not in host:
        logger.fatal("Username@IP is minimal requirement")
        raise ValueError("host name %s is not correct" % host)
    try:
        username, hostname = host.split("@")
        if " " in hostname:
            hostname, key = hostname.split(" ")
            key = pm.RSAKey.from_private_key_file(key)
        else:
            key = None  # use default
        if ":" in hostname:
            hostname, port = hostname.split(":")
            port = int(port)
        else:
            hostname = hostname
            port = 22
    except Exception as e:
        logger.fatal("Catch other error when parsing the remote resource configuration.  Check documentation please.")
        raise e
    return username, hostname, port, key


class Remote(object):  # pragma: no cover
    def __init__(self, host):
        """
        parse host name string into full host spec:
        `username@ip` or `username@ip:port` or `username@ip ssh_key` or `username@ip:port ssh_key`
        :param host: host name string
        """
        self.username, self.hostname, self.port, self.key = parse_hostname(host)

        client = pm.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(pm.AutoAddPolicy())
        self.client = client

    def __enter__(self):
        self.client.connect(self.hostname, self.port, self.username, pkey=self.key)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()


class SSHResourceManager(CPUResourceManager):  # pragma: no cover
    def __init__(self, connector, n_parallel, key="node_mapping", auppath=DEFAULT_AUPTIMIZER_PATH, **kwargs):
        """
        :param connector: SQL connector
        :param n_parallel: number of parallel jobs
        :param key: where to find the node assignment in aup env.ini
        :param auppath: aup environment path
        :param kwargs: experiment.json -> resource_args will be loaded here.
        """
        super(SSHResourceManager, self).__init__(connector, n_parallel)
        self.mapping = self.load_node_mapping(key=key, auppath=auppath)
        self.verified = set()
        self.remote_class = Remote

    @staticmethod
    def load_node_mapping(key="node_mapping", auppath=DEFAULT_AUPTIMIZER_PATH):
        """
        Loads ssh configurations from file.
        """
        config = load_default_env(auppath=auppath)
        check_missing_key(config, key, "Missing %s parameter in aup config" % key, log=logger)
        d = json.loads(config[key])
        logger.debug("Load resources %s", json.dumps(d))
        return {int(i): d[i] for i in d}

    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        # experiment.json -> runtime_args will be loaded here
        logger.debug("Job %d started on node %s", job.jid, self.mapping)
        overwrite = kwargs.get('overwrite', False)
        env = kwargs.get('env', {})
        logger.debug("Environment variables - %s", env)
        prescript = kwargs.get("prescript", "").strip()
        if prescript and prescript[-1] != ";":
            prescript += ";"
        postscript = kwargs.get("postscript", "").strip()
        if postscript and postscript[0] != ";":
            postscript = ";" + postscript

        def job_run():
            logger.debug("path:%s; script:%s", job.path, job.script)
            local_config = os.path.join(".", "jobs", "%d.json" % job.jid)
            local_out = os.path.join(".", "jobs", "%d.out" % job.jid)
            config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
            log_dump_path = os.path.join(job.path, "jobs", "%d.out" % job.jid)
            res = "ERROR"
            result = "workingdir:%s\njob:%s\n,config:%s" % (job.path, job.script, config_path)

            try:  # TODO-change it such that no need to keep ssh connection alive
                with self.remote_class(self.mapping[rid]) as remote:
                    if rid not in self.verified:
                        job.verify_remote(remote, overwrite=overwrite)
                        self.verified.add(rid)
                    job.config.save(local_config)
                    sftp = remote.open_sftp()
                    sftp.put(local_config, config_path)
                    logger.debug("Running the following commands- ")
                    command = "%scd %s;%s %s >%s 2>&1;cat %s%s" % \
                              (prescript, job.path, job.script, config_path, log_dump_path, log_dump_path, postscript)
                    logger.debug(command)
                    result = remote.exec_command(command, environment=env)[1]
                    result.channel.recv_exit_status()   # block
                    sftp.get(log_dump_path, local_out)
                    sftp.close()
                    result = result.read().decode(sys.stdin.encoding)
                    logger.debug(result)
                    res = parse_result(result)
            except ValueError:
                logger.fatal("Failed to parse result, check %s at local, or %s at remote", local_out, log_dump_path)
            except pm.SSHException as e:
                logger.fatal("Failed to run job over ssh due to unknown reason: %s", str(e))
                logger.fatal("%s", result)
            except Exception as e:
                logger.fatal("catch unexpected error %s", e)
                logger.fatal("%s", result)
            finally:
                logger.debug("return %s,%d", res, job.jid)
            return res, job.jid

        def call_back(future3):
            logger.debug("Callback for job %d", job.jid)
            try:
                self.lock.acquire(True)
                if future3.exception():  # If error happens, please report.  It is tricky to debug here.
                    logger.fatal("Error happened in job execution that not captured.")
                    logger.fatal(future3.exception())
                result = future3.result()
                logger.debug("Callback result: %s", result.__str__())
                self.running.pop(self.running.index(future3))
                call_back_func(*result)
            finally:
                self.lock.release()

        future = self.executor.submit(job_run)
        self.running.append(future)
        future.add_done_callback(call_back)
