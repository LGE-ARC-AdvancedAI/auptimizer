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
from concurrent.futures import ThreadPoolExecutor
import sys

from .AbstractResourceManager import AbstractResourceManager
from ...utils import parse_result

logger = logging.getLogger(__name__)


class CPUResourceManager(AbstractResourceManager):
    def __init__(self, connector, n_parallel, *args, **kwargs):
        super(CPUResourceManager, self).__init__(connector, *args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=n_parallel)
        self.n_parallel = n_parallel
        self.lock = threading.Lock()
        self.running = []

    def finish(self, eid, maximize=True):
        self.executor.shutdown(wait=True)
        return super(CPUResourceManager, self).finish(eid, maximize)

    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        job.verify_local()

        if "env" not in kwargs:
            # make sure not over step on GPUs
            kwargs["env"] = os.environ
            kwargs["env"]["CUDA_VISIBLE_DEVICES"] = "-1"
        else:
            kwargs["env"] = kwargs["env"]

        def job_run():
            logger.debug("Job %d started" % job.jid)
            config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
            log_dump_path = os.path.join(job.path, "jobs", "%d.%d.out" % (job.jid, job.curr_retries))
            job.config.save(config_path)
            res = "ERROR"
            result = "%s\n%s" % (job.script, config_path)
            try:
                script = job.script.split(" ") + [config_path]
                result = subprocess.check_output(script, cwd=job.path, stderr=subprocess.STDOUT,
                                                 **kwargs)
                res = parse_result(result.decode(sys.stdin.encoding if sys.stdin.encoding is not None else 'UTF-8'))
            except ValueError:
                logger.fatal("Failed to parse result, check %s", 
                    os.path.join(job.path, "jobs", "%d.*.out" % job.jid))
            except subprocess.CalledProcessError as e:
                logger.fatal("Failed to run job:\n%s", result)
                result = e.output
            except Exception as e:  # pragma: no cover
                logger.fatal("Failed to run job:\n%s", result)
                logger.fatal("Error message might not be right: %s", e)
                result = str.encode(str(e))
            finally:
                with open(log_dump_path, 'wb') as fp:
                    fp.write(result)
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
        self.running.append(future)
        future.add_done_callback(call_back) 
