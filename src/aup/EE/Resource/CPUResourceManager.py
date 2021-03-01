"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
  
aup.EE.Resource.CPUResourceManager
==================================

Resource Manager for CPUs on a single machine.

However, user can specify arbitrary number for parallel computing, no real control of resources (yet).

APIs
----
"""
import logging
import os
import subprocess
import threading
import sys
import json
from numpy import random

from .AbstractResourceManager import AbstractResourceManager
from ...utils import parse_result, parse_one_line
from .AbstractResourceManager import _SupportResource
from ...aup import BasicConfig
from ..Job import Job
from .utils.ResourceThreadPoolExecutor import ResourceThreadPoolExecutor

logger = logging.getLogger(__name__)


class CPUResourceManager(AbstractResourceManager):
    def __init__(self, connector, n_parallel, *args, **kwargs):
        super(CPUResourceManager, self).__init__(connector, n_parallel, *args, **kwargs)
        self.executor = ResourceThreadPoolExecutor(max_workers=n_parallel)
        self.n_parallel = n_parallel
        self.lock = threading.Lock()
        self.running = []
        self.save_model = kwargs.get('save_model', False)
        self.script = kwargs.get('script', None)
        self.workingdir = kwargs.get('workingdir', None)
        self.one_shot = kwargs.get("one_shot", False)
        self.runtime_args = kwargs.get('runtime_args', {})

    def finish(self, maximize=True, status="FINISHED"):
        self.executor.shutdown(wait=True)
        best_result = super(CPUResourceManager, self).finish(status)

        self.connector.free_all_resources()

        if self.save_model is True and best_result is not None and status == 'FINISHED':
            logger.info("Experiment finished, starting best job")

            # re-run the best job, but also save the model on the disk
            self.executor = ResourceThreadPoolExecutor(max_workers=1)
            best_job_config_str = self.connector.get_best_result_config(self.eid, self.maximize)
            best_job_config = BasicConfig()
            best_job_config.update(json.loads(best_job_config_str[0]))
            best_job_config['save_model'] = True
            best_job_config['folder_name'] = 'models_{}'.format(self.eid)

            # todo improve
            _rtype = None
            for res, cname in _SupportResource.items():
                if cname == self.__class__.__name__:
                    _rtype = res
                    break

            # all should be free, but just in case
            rids = self.connector.get_available_resource(None, _rtype)
            free_rid = random.choice(rids) if rids else None
            best_job = Job(self.script, best_job_config, self.workingdir)
            # special job id for best job
            best_job.jid = best_result[0]

            def best_job_callback(score, jid):
                if score != 'ERROR':
                    logger.info("Best job finished, please check aup_models/models_{} folder".format(self.eid))

            self.run(best_job, free_rid, None, best_job_callback, **self.runtime_args)

            self.executor.shutdown(wait=True)

        return best_result

    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        if "env" not in kwargs:
            # make sure not over step on GPUs
            kwargs["env"] = os.environ
            # todo -1 or empty?
            kwargs["env"]["CUDA_VISIBLE_DEVICES"] = ""
        else:
            kwargs["env"] = kwargs["env"]

        def job_run():
            logger.debug("Job %d started" % job.jid)
            save_model_flag = job.config.get('save_model', False)
            config_path = None
            log_dump_path = None
            result = None
            res = "ERROR"
            proc = None
            script = None
            output = None

            try:
                if save_model_flag is not True or self.one_shot:
                    config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
                    log_dump_path = os.path.join(job.path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
                else:
                    config_path = os.path.join(job.path, "jobs", 'best_job_%d.json' % self.eid)
                    log_dump_path = os.path.join(job.path, "jobs", "best_job_%d.out" % self.eid)

                result = "%s\n%s" % (job.script, config_path)

                job.verify_local()
                job.config.save(config_path)

                script = job.script.split(" ") + [config_path]
                proc = subprocess.Popen(script, cwd=job.path,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        **kwargs)
                output = ""
                with open(log_dump_path, 'w') as fp:
                    while True:
                        if self.is_job_stopped(job.jid) == True:
                            proc.kill()
                            raise StopIteration()

                        line = proc.stdout.readline()
                        if not line:
                            break

                        line_str = line.decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8')
                        output += line_str

                        interm_res = parse_one_line(line_str)
                        if interm_res != None:
                            res = interm_res[0]
                            irid = self.append_interm_res(job.jid, interm_res[0])
                            self.append_multiple_results(job.jid, irid, self.eid, interm_res[1:])

                        # continuously write to jid.out file
                        fp.write(line_str)

                # set the flag in multiple_result table
                self.set_last_multiple_results(self.eid, job.jid)

                if res == "ERROR":
                    raise ValueError

            except StopIteration:
                logger.debug("Job stopped")
                res = "EARLY STOPPED"
            except ValueError:
                logger.fatal("Failed to parse result, check %s", log_dump_path)
            except subprocess.CalledProcessError as e:
                logger.fatal("Failed to run job:\n%s", result)
                output = e.output
            except (Exception, EnvironmentError) as e:  # pragma: no cover
                logger.fatal("Failed to run job:\n%s", result)
                logger.fatal("Error message might not be right: %s", e)
                output = str(e)
            finally:
                if res == "ERROR" and output is not None:
                    self.log_error_message(output)
                # should be already terminated, but just in case
                if proc is not None:
                    proc.kill()

                return res, job.jid

        def call_back(future3):
            """
            Use to collect result. Don't change.
            """
            logger.debug("Callback for job %d" % job.jid)
            try:
                self.lock.acquire(True)
                if future3.exception():
                    logger.fatal("Error happened with job script with following error message (not reliable)")
                    logger.fatal(type(future3.exception()))
                    logger.fatal(future3.exception())
                    raise ChildProcessError
                result = future3.result()
                logger.debug("Callback result: %s" % result.__str__())
                call_back_func(*result)
            except ChildProcessError:
                logger.fatal("Use ctrl+c to stop experiment")
            finally:
                self.running.pop(self.running.index(future3))
                self.lock.release()

        future = self.executor.submit(job_run)
        if future is not None:
            self.running.append(future)
            future.add_done_callback(call_back) 
