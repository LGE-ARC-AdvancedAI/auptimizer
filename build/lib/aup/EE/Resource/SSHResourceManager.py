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
import time

import paramiko as pm

from .CPUResourceManager import CPUResourceManager
from ...utils import check_missing_key, load_default_env, parse_result, DEFAULT_AUPTIMIZER_PATH, block_until_ready
from ...utils import open_sftp_with_timeout
from ..Job import Job

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

    def exec_command(self, command, command_async=None, *args, **kwargs):
        return self.client.exec_command(command, *args, **kwargs)

    def __enter__(self):
        self.client.connect(self.hostname, self.port, self.username, pkey=self.key,
                            timeout=5, auth_timeout=5, banner_timeout=5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()


class SSHResourceManager(CPUResourceManager):  # pragma: no cover
    def __init__(self, connector, n_parallel, key="node_mapping", auppath=DEFAULT_AUPTIMIZER_PATH, 
                 async_run=False, async_reconnect=30, async_timeout=None, 
                 reconn_wait_time=30, max_retries=3, **kwargs):
        """
        :param connector: SQL connector
        :param n_parallel: number of parallel jobs
        :param key: where to find the node assignment in aup env.ini
        :param auppath: aup environment path
        :param async_run: whether the ssh job should be run asynchronously
        :param async_reconnect: number of seconds to reconnect and check job status of async job
        :param async_timeout: maximum number of seconds to try reconnection to the async job, otherwise failure
        :param reconn_wait_time: for non-async jobs, maximum number of seconds to try reconnection to the job, otherwise failure
        :param max_retries: for both async and non-async jobs, maximum number of retries for each job.
        :param kwargs: experiment.json -> resource_args will be loaded here.
        """
        super(SSHResourceManager, self).__init__(connector, n_parallel)
        self.mapping = self.load_node_mapping(key=key, auppath=auppath)
        self.verified = set()
        self.remote_class = Remote
        self._async_run = async_run
        self._async_reconnect = async_reconnect
        self._async_timeout = async_timeout
        self._wait_time = reconn_wait_time
        self._n_tries = max_retries

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
            curr_number_of_tries = 0
            time_job_start = time.time()
            logger.debug("path:%s; script:%s", job.path, job.script)
            local_script = job.script.split()[0]
            local_job_path = os.path.join(os.path.dirname(local_script))
            local_config = os.path.join(local_job_path, "jobs", "%d.json" % job.jid)
            local_out = os.path.join(local_job_path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
            config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
            log_dump_path = os.path.join(job.path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
            done_file_path = os.path.join(job.path, "jobs", "%d.done" % job.jid)
            res = "ERROR"
            result = "workingdir:%s\njob:%s\n,config:%s" % (job.path, job.script, config_path)
            
            # Auptimizer tries to run each job over ssh connection, 'max_retries' number of times.
            # This is to handle and failure with connection issues or issues due to running over remote machine.
            while curr_number_of_tries < self._n_tries:
                try:
                    with self.remote_class(self.mapping[rid]) as remote:
                        if rid not in self.verified:
                            job.verify_remote(remote, overwrite=overwrite)
                            self.verified.add(rid)
                        job.config.save(local_config)
                        sftp = open_sftp_with_timeout(remote.client, 5)

                        # The job is run by copying over the script and required context, along with setting up the correct environments and preprocessing and post processing scripts.
                        
                        stdout = None
                        if job.was_executed == False:
                            sftp.put(local_config, config_path)

                            logger.debug("Running the following commands- ")
                            if self._async_run:
                                command = "%scd %s; rm -f %s; ((./%s %s >%s 2>&1 && echo '1' > %s) || echo '0' > %s; cat %s%s) &" % \
                                        (prescript, job.path, done_file_path, os.path.basename(job.script), config_path, log_dump_path, done_file_path, done_file_path, log_dump_path, postscript)
                            else:
                                command = "%scd %s; ./%s %s >%s 2>&1; cat %s%s" % \
                                        (prescript, job.path, os.path.basename(job.script), config_path, log_dump_path, log_dump_path, postscript)
                            logger.debug(command)
                            stdin, stdout, stderr = remote.exec_command(command, environment=env)
                            block_until_ready(remote.client, stdout, env)
                            stdout.channel.recv_exit_status()   # block #TODO entry for issue regarding persistence

                            job.was_executed = True
                            
                        # Jobs that are run with async as true, run using an asynchronous agent, which reconnects every 'async_timeout' seconds to check if the job has finished. 

                        if not self._async_run:
                            sftp.get(log_dump_path, local_out)
                            sftp.close()
                            result = ""
                            if stdout is not None:
                                result = stdout.read().decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8')
                                
                    # The async job and Auptimizer correspond using a dummy log outputfile ('done_file_path'). 
                    # Auptimizer checks the async job for timeout, success or failure using different encodings.  
                    timedout = False
                    done_status = True
                    if self._async_run:
                        check_command = "test -f %s && cat %s" % (done_file_path, done_file_path)
                        with self.remote_class(self.mapping[rid]) as remote:
                            _, stdout, _ = remote.exec_command(check_command, environment=env)
                            block_until_ready(remote.client, stdout, env)
                            ret = stdout.channel.recv_exit_status()
                        while ret:
                            if self._async_timeout is not None and time.time() - time_job_start > self._async_timeout:
                                logger.critical("Asynchronous job timed out")
                                timedout = True
                                break
                            time.sleep(self._async_reconnect)
                            logger.info("Checking job status")
                            with self.remote_class(self.mapping[rid]) as remote:
                                stdin, stdout, _ = remote.exec_command(check_command, environment=env)
                                block_until_ready(remote.client, stdout, env)
                                ret = stdout.channel.recv_exit_status()
                                done_status = bool(stdout.read().decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8'))
                        
                        if not timedout and done_status:
                            logger.info("Job finished, parsing result")
                            with self.remote_class(self.mapping[rid]) as remote:
                                sftp = remote.client.open_sftp()
                                sftp.get(log_dump_path, local_out)
                                sftp.close()
                                with open(local_out, "r") as f:
                                    result = f.read()

                    if timedout or not done_status:
                        res = "ERROR"
                    else:
                        logger.debug(result)
                        res = parse_result(result)
                except ValueError as e:
                    logger.fatal("Failed to parse result, check %s files at local, or %s at remote", 
                        os.path.join(local_job_path, "jobs", "%d.*.out" % job.jid),
                        os.path.join(job.path, "jobs", "%d.*.out" % job.jid))
                    break
                except pm.SSHException as e:
                    logger.fatal("Failed to run job over ssh due to unknown reason: %s", str(e))
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    continue
                except Exception as e:
                    logger.fatal("catch unexpected error %s", e)
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    continue
                if job.was_executed == True:
                    logger.debug("return %s,%d", res, job.jid)
                    break
            if res == "ERROR":
                logger.fatal("Unable to run job with id: "+str(job.jid))
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
