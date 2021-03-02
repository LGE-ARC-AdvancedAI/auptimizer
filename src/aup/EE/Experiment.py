"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Experiment module
========================

:mod:`aup.EE.Experiment` is called by `aup.__main__` to start an experiment.

See :doc:`algorithm` for configuration specification.

APIs
----
"""

import json
import logging
import os
import signal
import sys
import _thread
import threading
import time

from ..Proposer import get_proposer, SPECIAL_EXIT_PROPOSERS
from .Job import Job
from .Resource import get_resource_manager
from ..aup import BasicConfig
from ..utils import set_default_keyvalue, check_missing_key, get_default_connector, get_default_username
from ..compression.utils import *
from ..Proposer import ProposerStatus

logger = logging.getLogger(__name__)


def _verify_config(config):
    """
    verify the experiment configuration is fulfilled for experiment

    :param config: experiment configuration
    :return: config if verified
    """
    check_missing_key(config, "script", "Missing required value for 'script'.", log=logger)
    check_missing_key(config, "resource", "Missing required value for 'resource'", log=logger)
    check_missing_key(config, "name", "Missing required value for 'name'", log=logger)
    return config


class Experiment:
    """
    Experiment Class - create and run an experiment

    :param exp_config: configuration of the experiment
    :type exp_config: BasicConfig.BasicConfig
    :param username: username, default: None - will use login username
    :type username: str
    :param connector: connector to database
    :type connector: AbstractConnector
    :param auppath: Auptimizer env.ini file folder, default is either ``./.aup`` or ``~/.aup``
    :type auppath: str
    :param sleep_time: time to pause between jobs
    :type sleep_time: int
    """

    def __init__(self,
                 exp_config,
                 username=None,
                 connector=None,
                 auppath=os.path.join(".aup"),
                 sleep_time=1,
                 eid=None,
                 start=True,
                 request_stop_time=5):
        self.sleep_time = sleep_time
        self.fail_safe = False
        self.job_retries = 0
        self.exp_config = _verify_config(exp_config)
        self.resource_args = None
        self.connector = connector if connector else get_default_connector(auppath=auppath, log=logger)
        self.username = get_default_username(username)
        self.is_compression_exp = False
        self.compression_params = []
        self.request_stop_thr = None
        self.request_stop_time = request_stop_time
        self.submitted = False

        if "job_failure" in self.exp_config:
            set_default_keyvalue("ignore_fail", False, self.exp_config["job_failure"], log=logger)
            set_default_keyvalue("job_retries", 3, self.exp_config["job_failure"], log=logger)
            self.fail_safe = self.exp_config["job_failure"]["ignore_fail"]
            self.job_retries = self.exp_config["job_failure"]["job_retries"]

        if "compression" in self.exp_config:
            self.is_compression_exp = True
            self.exp_config, self.compression_params = translate_compression_config(self.exp_config)

        set_default_keyvalue("cwd", os.getcwd(), self.exp_config, log=logger)
        set_default_keyvalue("workingdir", os.getcwd(), self.exp_config, log=logger)
        set_default_keyvalue("n_parallel", 1, self.exp_config, log=logger)
        check_missing_key(self.exp_config, "target", "Specify max/min for target", log=logger)
        check_missing_key(self.exp_config, "proposer", "Specify the optimization `proposer`", log=logger)
        self.proposer = get_proposer(self.exp_config['proposer'])(self.exp_config)
        if "resource_args" in self.exp_config:
            if "early_stop" in self.exp_config["resource_args"]:
                self.exp_config["resource_args"]["track_intermediate_results"] = True
            self.resource_manager = get_resource_manager(self.exp_config["resource"], self.connector,
                                                         self.exp_config["n_parallel"], auppath=auppath,
                                                         maximize=(self.exp_config["target"] == "max"),
                                                         **self.exp_config["resource_args"],
                                                         workingdir=self.exp_config['workingdir'],
                                                         script=self.exp_config['script'],
                                                         runtime_args = exp_config.get('runtime_args', {}))
            self.resource_args = self.exp_config["resource_args"]
        else:
            self.resource_manager = get_resource_manager(self.exp_config["resource"], self.connector,
                                                         self.exp_config["n_parallel"], auppath=auppath,
                                                         maximize=(self.exp_config["target"] == "max"),
                                                         workingdir=self.exp_config['workingdir'],
                                                         script=self.exp_config['script'],
                                                         runtime_args = exp_config.get('runtime_args', {}))
        if eid is None:
            if start is True:
                self.eid = self.resource_manager.connector.start_experiment(self.username, self.exp_config)
            else:
                self.eid = self.resource_manager.connector.create_experiment(self.username, self.exp_config)
        else:
            self.eid = eid
            self.resource_manager.connector.start_experiment_by_eid(self.eid)
        self.resource_manager.eid = self.eid
        self.pending_jobs = {}
        if 'runtime_args' in exp_config:
            self.runtime_args = exp_config['runtime_args']
        else:
            self.runtime_args = {}
        logger.info("Experiment %d is created" % self.eid)
        logger.debug("Experiment config is %s" % json.dumps(self.exp_config))

    def add_suspend_signal(self):
        signal.signal(signal.SIGINT, lambda x, y: self._suspend(x, y))

    def add_refresh_signal(self):
        signal.signal(signal.SIGUSR1, lambda x, y: self._force_refresh(x, y))

    def finish(self):
        """
        Finish experiment if no job is running

        :return: job id, best score
        :rtype: (int, float)
        """
        while self.proposer.get_status() == ProposerStatus.RUNNING:
            logger.debug("Waiting for proposer")
            time.sleep(self.sleep_time)

        while len(self.pending_jobs) != 0:
            # resource manager will prevent experiment shutdown with pending jobs.
            # but just in case
            logger.debug("Waiting for pending job")
            time.sleep(self.sleep_time)

        result = self.resource_manager.finish(status=self.proposer.get_status().name)
        self.connector.close()

        if self.request_stop_thr is not None:
            self.request_stop_thr.join()

        if result is None or len(result) == 0:
            logger.warning("No result so far")
            return None, -1
        else:
            logger.info("Finished")
            logger.critical("Best job (%d) with score %f in experiment %d" % (result[0], result[1], self.eid))
            try:
                self.proposer.save(os.path.join(".", "exp%d.pkl" % self.eid))
            except NotImplementedError:
                pass
            return result[:2]

    def resume(self, filename):
        """
        Restore previous experiment, previous job during suspension won't be run in this round

        :param filename: filename (saved by pickle as exp%d.pkl)
        :type filename: str
        """
        self.proposer.reload(filename)   # Note: previously failed jobs won't be execute again.
        self.start()

    def start(self):
        """
        Start experiment
        """
        remaining_jobs = self.proposer.get_remaining_jobs()
        parallel_jobs = min(remaining_jobs, self.exp_config.n_parallel)

        self.request_stop_thr = threading.Thread(target=self._check_status)
        self.request_stop_thr.start()

        for i in range(parallel_jobs - len(self.pending_jobs)):
            rc = self.submit_job()
            self.submitted = self.submitted or rc
            if not self.submitted:
                logger.fatal("No job is running; quit")
                self.proposer.set_status(ProposerStatus.FAILED)
                raise Exception("Cannot run experiment!")
            elif not rc:
                logger.warning("Job submission failed, keep running")

    def submit_job(self, job=None, rid_blacklist=None):
        """
        Submit a new job to run if there is resource available
        :param job: optional job parameter in case a job needs resubmitting
        :type job: aup.EE.Job.Job object
        :param rid_blacklist: resource ids to exclude when submitting job
        :type rid_blacklist: [int]

        :return: True if job submitted, else False
        """
        rid = self.resource_manager.get_available(self.username, self.exp_config["resource"], rid_blacklist=rid_blacklist)
        if rid is None:
            self.resource_manager.log_error_message("Not enough resources!")
            logger.warning("Increase resource or reduce n_parallel, no enough resources")
            return False

        if job is None:
            proposal = self.proposer.get()
            if proposal is not None and self.is_compression_exp:
                proposal = deserialize_compression_proposal(self.exp_config, self.compression_params, proposal)
            self.proposer.increment_job_counter()
        if job is None and proposal is None:
            if self.exp_config['proposer'] in SPECIAL_EXIT_PROPOSERS:
                logger.info("%s is waiting to finish." % self.exp_config['proposer'])
                return True
            else:
                logger.warning("Waiting other jobs finished\n"
                               "Think about rebalance your task loads, if you see this message shows up too many")
                return False
        else:
            if job is None:
                job_config = BasicConfig(**proposal)
                job = Job(self.exp_config["script"], job_config, self.exp_config["workingdir"], retries=self.job_retries)
                job.jid = self.resource_manager.connector.job_started(self.eid, rid, job_config)
            else:
                self.resource_manager.connector.job_retry(rid, job.jid)
            logger.info("Submitting job %d with resource %d in experiment %d" % (job.jid, rid, self.eid))
            job.was_executed = False
            self.pending_jobs[job.jid] = job
            # update the status, but after appending to pending_jobs
            # to avoid premature termination
            self.proposer.check_termination()
            self.resource_manager.run_job(job, rid, self.exp_config, self.update, **self.runtime_args)
            return True

    def update(self, score, jid):
        """
        Callback function passed to :mod:`aup.EE.Resource.AbstractResourceManager` to
         update the job history (also proposer and connector)

        :param score: score returned from job (using :func:`aup.utils.print_result`)
        :type score: float
        :param jid: job id
        :type jid: int
        """
        if score == "ERROR":
            job = self.pending_jobs.pop(jid)
            if job.jid in self.resource_manager.jobs and \
                job.curr_retries < job.retries:
                rid = self.resource_manager.jobs[jid]
                job.rid_blacklist.add(rid)
                self.resource_manager.connector.job_failed(rid, jid)
                job.curr_retries += 1
                logger.info("Retrying job %d (%d/%d)" % (jid, job.curr_retries, job.retries))
                self.submit_job(job, rid_blacklist=job.rid_blacklist)
            elif not self.fail_safe:
                self.resource_manager.finish_job(jid, None, "FAILED")
                self.proposer.set_status(ProposerStatus.FAILED)
                logger.fatal("Stop Experiment due to job failure (ignore_fail flag set to false)")
            else:
                self.resource_manager.finish_job(jid, None, "FAILED")
                try:
                    self.proposer.failed(job)
                except Exception as ex:
                    self.proposer.set_status(ProposerStatus.FAILED)
                    logger.fatal("Stop Experiment due to job failure (failed jobs unsupported by proposer)")
                logger.info("Job %d is finished (failed)" % (jid))
                if self.proposer.get_status() == ProposerStatus.RUNNING:
                    self.start()
        elif score == "EARLY STOPPED":
            self.pending_jobs.pop(jid)
            self.resource_manager.finish_job(jid, score, "EARLY_STOPPED")
            logger.info("Job %d was early stopped" % (jid))
            if self.proposer.get_status() == ProposerStatus.RUNNING:
                self.start()
        else:
            self.proposer.update(score, self.pending_jobs[jid])
            self.pending_jobs.pop(jid)
            self.resource_manager.finish_job(jid, score, "FINISHED")
            logger.info("Job %d is finished with result %s" % (jid, score))

            if self.proposer.get_status() == ProposerStatus.RUNNING:
                self.start()

    def _suspend(self, sig, frame):
        """
        Stop experiment by enter "Ctrl-C"
        """
        logger.fatal("Experiment ended at user's request")
        for i in self.pending_jobs:
            logger.warning("Job with ID %d is cancelled" % i)         # Note: cancelled job won't be run again.
        try:
            self.proposer.save(os.path.join(".", "exp%d.pkl" % self.eid))
        except NotImplementedError:
            pass
        self.resource_manager.suspend()
        result = self.resource_manager.finish(status="STOPPED")
        self.connector.close()
        if result is None:
            logger.warning("No valid result so far")
        else:
            logger.critical("Best job (%d) with score %f in experiment %d" % (result[0], result[1], self.eid))
        if self.request_stop_thr is not None:
            self.request_stop_thr.join()
        sys.exit(1)

    def _check_status(self):
        """
        Checks the database status of the experiment for external stopping requests

        This method is run continuously in a separate "clean-up" thread in order to check for
        external modifications to the experiment status in the database, in case a user
        wants to stop an experiment remotely (e.g. from another process).
        """
        if self.connector is None or self.eid is None:
            logger.warning("Could not start thread for checking external experiment stopping requests.")
            return

        while True:
            try:
                if self.connector.is_closed():
                    logger.debug("Closing down clean-up thread.")
                    return

                status = self.connector.maybe_get_experiment_status(self.eid)
                if status == "REQUEST_STOP":
                    return _thread.interrupt_main()

                time.sleep(self.request_stop_time)
            except Exception as ex:
                logger.debug("Error in clean-up thread: {}".format(ex))

    def _force_refresh(self, sig, frame):
        # currently useful for async resource manager timers
        self.resource_manager.refresh()
