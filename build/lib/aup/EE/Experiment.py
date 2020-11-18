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
import time

from ..Proposer import get_proposer, SPECIAL_EXIT_PROPOSERS
from .Job import Job
from .Resource import get_resource_manager
from ..aup import BasicConfig
from ..utils import set_default_keyvalue, check_missing_key, get_default_connector, get_default_username

logger = logging.getLogger(__name__)


def _verify_config(config):
    """
    verify the experiment configuration is fulfilled for experiment

    :param config: experiment configuration
    :return: config if verified
    """
    check_missing_key(config, "script", "Missing required value for 'script'.", log=logger)
    check_missing_key(config, "resource", "Missing required value for 'resource'", log=logger)
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
                 sleep_time=1):
        self.sleep_time = sleep_time
        self.fail_safe = False
        self.job_retries = 0
        self.exp_config = _verify_config(exp_config)
        self.connector = connector if connector else get_default_connector(auppath=auppath, log=logger)
        self.username = get_default_username(username)

        if "job_failure" in self.exp_config:
            set_default_keyvalue("ignore_fail", False, self.exp_config["job_failure"], log=logger)
            set_default_keyvalue("job_retries", 0, self.exp_config["job_failure"], log=logger)
            self.fail_safe = self.exp_config["job_failure"]["ignore_fail"]
            self.job_retries = self.exp_config["job_failure"]["job_retries"]

        set_default_keyvalue("workingdir", os.getcwd(), self.exp_config, log=logger)
        set_default_keyvalue("n_parallel", 1, self.exp_config, log=logger)
        check_missing_key(self.exp_config, "target", "Specify max/min for target", log=logger)
        check_missing_key(self.exp_config, "proposer", "Specify the optimization `proposer`", log=logger)
        self.proposer = get_proposer(self.exp_config['proposer'])(self.exp_config)
        if "resource_args" in self.exp_config:
            self.resource_manager = get_resource_manager(self.exp_config["resource"], self.connector,
                                                         self.exp_config["n_parallel"], auppath=auppath,
                                                         **self.exp_config["resource_args"])
        else:
            self.resource_manager = get_resource_manager(self.exp_config["resource"], self.connector,
                                                         self.exp_config["n_parallel"], auppath=auppath)
        self.eid = self.resource_manager.connector.start_experiment(self.username, json.dumps(self.exp_config))
        self.pending_jobs = {}
        if 'runtime_args' in exp_config:
            self.runtime_args = exp_config['runtime_args']
        else:
            self.runtime_args = {}
        signal.signal(signal.SIGINT, lambda x, y: self._suspend(x, y))
        logger.info("Experiment %d is created" % self.eid)
        logger.debug("Experiment config is %s" % json.dumps(self.exp_config))

    def finish(self):
        """
        Finish experiment if no job is running

        :return: job id, best score
        :rtype: (int, float)
        """
        while not self.proposer.finished:
            logger.debug("Waiting for proposer")
            time.sleep(self.sleep_time)

        while len(self.pending_jobs) != 0:
            # resource manager will prevent experiment shutdown with pending jobs.
            # but just in case
            logger.debug("Waiting for pending job")
            time.sleep(self.sleep_time)

        result = self.resource_manager.finish(self.eid, maximize=(self.exp_config["target"] == "max"))
        self.connector.close()

        if len(result) == 0:
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
        for i in range(self.exp_config.n_parallel - len(self.pending_jobs)):
            submitted = self.submit_job()
            if self.fail_safe and not submitted:
                if i == 0:
                    logger.fatal("No job is running; quit")
                    exit(1)
                else:
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
            logger.warning("Increase resource or reduce n_parallel, no enough resources")
            return False

        if job is None:
            proposal = self.proposer.get()
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
                self.resource_manager.finish_job(jid, None)
                self.proposer.finished = True
                logger.fatal("Stop Experiment due to job failure (ignore_fail flag set to false)")
            else:
                self.resource_manager.finish_job(jid, None)
                try:
                    self.proposer.failed(job)
                except Exception as ex:
                    self.proposer.finished = True
                    logger.fatal("Stop Experiment due to job failure (failed jobs unsupported by proposer)")
                logger.info("Job %d is finished (failed)" % (jid))
                if not self.proposer.finished:
                    self.start()
        else:
            self.proposer.update(score, self.pending_jobs[jid])
            self.pending_jobs.pop(jid)
            self.resource_manager.finish_job(jid, score)
            logger.info("Job %d is finished with result %s" % (jid, score))

            if not self.proposer.finished:
                self.start()

    def _suspend(self, sig, frame):
        """
        Stop experiment by enter "Ctrl-C"
        """
        logger.fatal("Experiment ended at user's request")
        for i in self.pending_jobs:
            logger.warning("Job with ID %d is cancelled" % i)         # Note: cancelled job won't be run again.
        self.proposer.save(os.path.join(".", "exp%d.pkl" % self.eid))
        self.resource_manager.suspend()
        result = self.resource_manager.finish(self.eid, maximize=(self.exp_config["target"] == "max"))
        if result is None:
            logger.warning("No valid result so far")
        else:
            print("Best job (%d) with score %f in experiment %d" % (result[0], result[1], self.eid))
        sys.exit(1)
