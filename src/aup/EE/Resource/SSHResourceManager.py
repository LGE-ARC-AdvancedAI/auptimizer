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
import threading

import paramiko as pm

from .CPUResourceManager import CPUResourceManager
from ...utils import check_missing_key, load_default_env, parse_result, DEFAULT_AUPTIMIZER_PATH, block_until_ready
from ...utils import open_sftp_with_timeout, parse_one_line
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
                async_reconnect=30, async_timeout=None,
                async_run=False, reconn_wait_time=30, max_retries=3, **kwargs):
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
        super(SSHResourceManager, self).__init__(connector, n_parallel, **kwargs)
        self.mapping = self.load_node_mapping(key=key, auppath=auppath)
        self.verified = set()
        self.remote_class = Remote
        self._wait_time = reconn_wait_time
        self._n_tries = max_retries
        self._async_run = async_run
        self._async_reconnect = async_reconnect
        self._async_timeout = async_timeout
        # refresh rate of 1 second for async
        self._get_interm_res = 0.1
        self.refresh_lock = threading.Lock()
        self.s_passed_recon = 0
        self.s_passed_interm = 0

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

        curr_number_of_tries = 0
        logger.debug("path:%s; script:%s", job.path, job.script)
        local_script = job.script.split()[0]
        local_job_path = os.path.join(os.path.dirname(local_script))
        local_config = None
        local_out = None
        config_path = None

        save_model_flag = job.config.get('save_model', False)
        local_model_path = None
        remote_model_path = None
        log_dump_path = None
        # for async run
        done_file_path = None

        if save_model_flag is True and not self.one_shot:
            local_model_path = os.path.join(local_job_path, "aup_models", "models_{}".format(self.eid))
            remote_model_path = os.path.join(job.path, "aup_models", "models_{}".format(self.eid))
            config_path = os.path.join(job.path, "jobs", 'best_job_%d.json' % self.eid)
            log_dump_path = os.path.join(job.path, "jobs", "best_job_%d.out" % self.eid)
            local_config = os.path.join(local_job_path, "jobs", "best_job_%d.json" % self.eid)
            local_out = os.path.join(local_job_path, "jobs", "best_job_%d.out" % self.eid)
            done_file_path = os.path.join(job.path, "jobs", "best_job_%d.done" % self.eid)
        else:
            config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
            log_dump_path = os.path.join(job.path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
            local_config = os.path.join(local_job_path, "jobs", "%d.json" % job.jid)
            local_out = os.path.join(local_job_path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
            done_file_path = os.path.join(job.path, "jobs", "%d.done" % job.jid)

        result = "workingdir:%s\njob:%s\n,config:%s" % (job.path, job.script, config_path)
        res = "ERROR"

        # in case save_model is true
        def download_model_files(sftp, remote_dir, local_dir):
            from stat import S_ISDIR

            os.path.exists(local_dir) or os.makedirs(local_dir)
            dir_items = sftp.listdir_attr(remote_dir)
            for item in dir_items:
                remote_path = os.path.join(remote_dir, item.filename)
                local_path = os.path.join(local_dir, item.filename)
                if S_ISDIR(item.st_mode):
                    download_model_files(sftp, remote_path, local_path)
                else:
                    sftp.get(remote_path, local_path)

        def sync_job_run():
            nonlocal curr_number_of_tries
            nonlocal local_job_path
            nonlocal local_config
            nonlocal local_out
            nonlocal config_path
            nonlocal save_model_flag
            nonlocal local_model_path
            nonlocal remote_model_path
            nonlocal log_dump_path
            nonlocal res
            nonlocal result

            output = None

            # Auptimizer tries to run each job over ssh connection, 'max_retries' number of times.
            while curr_number_of_tries < self._n_tries:
                try:  # TODO-change it such that no need to keep ssh connection alive
                    with self.remote_class(self.mapping[rid]) as remote:
                        if rid not in self.verified:
                            job.verify_remote(remote, overwrite=overwrite)
                            self.verified.add(rid)
                        job.config.save(local_config)
                        sftp = open_sftp_with_timeout(remote.client, 5)

                        # The job is run by copying over the script and required context, along with setting up the correct environments and preprocessing and post processing scripts.

                        stdout = None
                        output = ""
                        if job.was_executed == False:
                            sftp.put(local_config, config_path)

                            logger.debug("Running the following commands- ")
                            command = "%scd %s; ./%s %s 2>&1 | tee %s%s" % \
                                        (prescript, job.path, os.path.basename(job.script), config_path, log_dump_path, postscript)
                            logger.debug(command)
                            stdin, stdout, stderr = remote.exec_command(command, environment=env)

                            with open(local_out, 'w') as fp:
                                while True:
                                    if self.is_job_stopped(job.jid) == True:
                                        sftp.close()
                                        raise StopIteration()

                                    line = stdout.readline()
                                    if not line:
                                        break
                                    output += line

                                    logger.debug(line)

                                    interm_res = parse_one_line(line)
                                    if interm_res != None:
                                        res = interm_res[0]
                                        irid = self.append_interm_res(job.jid, interm_res[0])
                                        self.append_multiple_results(job.jid, irid, self.eid, interm_res[1:])

                                    fp.write(line)

                            self.set_last_multiple_results(self.eid, job.jid)

                            job.was_executed = True

                        if save_model_flag is True:
                            download_model_files(sftp, remote_model_path, local_model_path)

                        sftp.close()

                    if res == "ERROR":
                        raise ValueError
                except StopIteration:
                    logger.info("Job stopped")
                    res = "EARLY STOPPED"
                    break
                except ValueError as e:
                    logger.fatal("Failed to parse result, check %s files at local, or %s at remote", 
                        local_out, log_dump_path)
                    break
                except pm.SSHException as e:
                    logger.fatal("Failed to run job over ssh due to unknown reason: %s", str(e))
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    output = str(e)
                    continue
                except Exception as e:
                    logger.fatal("catch unexpected error %s", e)
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    output = str(e)
                    continue
                if job.was_executed == True:
                    logger.debug("return %s,%d", res, job.jid)
                    break
            if res == "ERROR":
                if output is not None:
                    self.log_error_message(output)
                logger.fatal("Unable to run job with id: "+str(job.jid))
            return res, job.jid

        def async_job_run():
            nonlocal curr_number_of_tries
            nonlocal local_job_path
            nonlocal local_config
            nonlocal local_out
            nonlocal config_path
            nonlocal save_model_flag
            nonlocal local_model_path
            nonlocal remote_model_path
            nonlocal log_dump_path
            nonlocal done_file_path
            nonlocal res
            nonlocal result

            # touch local_out
            open(local_out, 'w').close()

            time_job_start = time.time()
            output = None

            while curr_number_of_tries < self._n_tries:
                try:  # TODO-change it such that no need to keep ssh connection alive
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
                            command = "%scd %s; rm -f %s; ((./%s %s >%s 2>&1 && echo '1' > %s) || echo '0' > %s%s) &" % \
                                    (prescript, job.path, done_file_path, os.path.basename(job.script), config_path, log_dump_path, \
                                        done_file_path, done_file_path, postscript)

                            logger.debug(command)
                            stdin, stdout, stderr = remote.exec_command(command, environment=env)
                            block_until_ready(remote.client, stdout, env)
                            stdout.channel.recv_exit_status()   # block #TODO entry for issue regarding persistence

                            job.was_executed = True

                    # Jobs that are run with async as true, run using an asynchronous agent, which reconnects every 'async_timeout' seconds to check if the job has finished
                    # The async job and Auptimizer correspond using a dummy log outputfile ('done_file_path').
                    # Auptimizer checks the async job for timeout, success or failure using different encodings.
                    done_status = False
                    check_command = "test -f %s && cat %s" % (done_file_path, done_file_path)
                    with self.refresh_lock:
                        self.s_passed_recon = 0
                        self.s_passed_interm = 0
                    num_lines = 0
                    ret = 1
                    start_time = time.time()
                    output = ""

                    while ret != 0:
                        end_time = time.time()
                        passed_time = (end_time - start_time)
                        with self.refresh_lock:
                            self.s_passed_recon += passed_time
                            self.s_passed_interm += passed_time

                        start_time = end_time

                        if self.is_job_stopped(job.jid) == True:
                            sftp.close()
                            raise StopIteration()

                        if self._async_timeout is not None and time.time() - time_job_start > self._async_timeout:
                            logger.critical("Asynchronous job timed out")
                            raise Exception("Job timedout")

                        # if the counter reached the async reconnect point
                        with self.refresh_lock:
                            if self.s_passed_recon > self._async_reconnect:
                                logger.debug("Checking job status")
                                with self.remote_class(self.mapping[rid]) as remote:
                                    stdin, stdout, _ = remote.exec_command(check_command, environment=env)
                                    block_until_ready(remote.client, stdout, env)
                                    ret = stdout.channel.recv_exit_status()
                                    done_status = bool(stdout.read().decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8'))

                                    self.s_passed_recon = 0
                        # if the counter reached the interm res gather or we finished the job
                        with self.refresh_lock:
                            if self.s_passed_interm > self._get_interm_res or ret == 0:
                                logger.debug("Getting the produced lines")
                                # get the last produced lines
                                get_interm_command = "tail -n \"$(($(cat %s | wc -l)-%d))\" %s" % \
                                    (log_dump_path, num_lines, log_dump_path)
                                with self.remote_class(self.mapping[rid]) as remote:
                                    stdin, stdout, _ = remote.exec_command(get_interm_command, environment=env)
                                    block_until_ready(remote.client, stdout, env)

                                    with open(local_out, 'a') as fp:
                                        while True:
                                            line = stdout.readline()
                                            if not line:
                                                break
                                            output += line

                                            num_lines += 1
                                            logger.debug(line)

                                            interm_res = parse_one_line(line)
                                            if interm_res != None:
                                                res = interm_res[0]
                                                irid = self.append_interm_res(job.jid, interm_res[0])
                                                self.append_multiple_results(job.jid, irid, self.eid, interm_res[1:])

                                            fp.write(line)

                                self.s_passed_interm = 0

                        # let other threads run
                        time.sleep(0.01)

                    # set the flag in multiple_result table
                    self.set_last_multiple_results(self.eid, job.jid)

                    with self.remote_class(self.mapping[rid]) as remote:
                        sftp = remote.client.open_sftp()

                        if save_model_flag is True:
                            download_model_files(sftp, remote_model_path, local_model_path)

                        sftp.close()
                    if not done_status:
                        res = "ERROR"

                    if res == "ERROR":
                        raise ValueError
                except StopIteration as si:
                    terminate_command = "kill $(ps -axo pid:1,cmd:2 | grep '%s %s$' | head -n 1 | cut -d' ' -f1)" % (os.path.basename(job.script), config_path)
                    with self.remote_class(self.mapping[rid]) as remote:
                        _, stdout, _ = remote.exec_command(terminate_command, environment=env)
                        block_until_ready(remote.client, stdout, env)
                        ret = stdout.channel.recv_exit_status()
                        if ret != 0:
                            logger.warning("Could not terminate remote process; possible hanging process remaining")
                    logger.info("Job stopped")
                    res = "EARLY STOPPED"
                    break
                except ValueError as e:
                    logger.fatal("Failed to parse result, check %s at local, or %s at remote", local_out, log_dump_path)
                    break
                except pm.SSHException as e:
                    logger.fatal("Failed to run job over ssh due to unknown reason: %s", str(e))
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    output = str(e)
                    continue
                except Exception as e:
                    logger.fatal("catch unexpected error %s", e)
                    logger.fatal("%s", result)
                    logger.fatal("Something went wrong, retrying job with id: "+str(job.jid))
                    curr_number_of_tries += 1
                    time.sleep(self._wait_time)
                    output = str(e)
                    continue
                if job.was_executed == True:
                    logger.debug("return %s,%d", res, job.jid)
                    break
            if res == "ERROR":
                if output is not None:
                    self.log_error_message(output)
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

        future = None
        if self._async_run is True:
            future = self.executor.submit(async_job_run)
        else:
            future = self.executor.submit(sync_job_run)

        if future is not None:
            self.running.append(future)
            future.add_done_callback(call_back)

    def refresh(self):
        # force a timer reset for async
        with self.refresh_lock:
            self.s_passed_recon = 2 * self._async_reconnect
            self.s_passed_interm = 2 * self._get_interm_res
