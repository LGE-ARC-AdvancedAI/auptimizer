"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.AbstractResourceManager
=======================================

Abstract Interface of Resource Managers.

Using :func:`get_resource_manager` to create the corresponding object with the following resource type.

For different resource supports, see :doc:`environment`.

APIs
----
"""
import abc
import copy
import importlib
import logging
import random
import threading
import time
import numpy as np
import math
import warnings

from ...utils import DEFAULT_AUPTIMIZER_PATH
from .utils.curve_fitting import CurveModel

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
EARLY_STOPPING_SLEEP = 1
CURVE_FITTING_MIN_ITS = 4
logger = logging.getLogger(__name__)

_SupportResource = {"gpu": "GPUResourceManager",
                    "cpu": "CPUResourceManager",
                    "node": "SSHResourceManager",
                    "aws": "AWSResourceManager",
                    "passive": "PassiveResourceManager"}


def get_resource_manager(resource, connector, n_parallel, auppath=DEFAULT_AUPTIMIZER_PATH, **kwargs):
    """
    Get resource manager for a specific resource type

    :param resource: gpu or cpu type resource
    :type resource: str
    :param connector: database connector
    :type connector: AbstractConnector
    :param n_parallel: how many parallel jobs to be run
    :type n_parallel: int
    :param auppath: aup environment folder
    :type auppath: str
    :return: resource manager
    :rtype: AbstractResourceManager
    """
    try:
        resource = _SupportResource[resource]
    except KeyError:
        raise KeyError("%s not implemented" % resource)

    mod = importlib.import_module(".%s" % resource, "aup.EE.Resource")
    return mod.__dict__[resource](connector, n_parallel, auppath=auppath, **kwargs)


class AbstractResourceManager(ABC):
    """
    Create Resource to run jobs.

    :param connector: Connector to database
    :type connector: AbstractConnector
    """

    def __init__(self, connector, n_parallel, *args, **kwargs):
        self.connector = connector
        self.jobs = dict()

        warnings.filterwarnings("ignore")

        self.curr_global_iteration = 0
        self.maximize = kwargs.get("maximize", True)
        self.stopped_jobs = None
        self.stopped_jobs_lock = threading.Lock()
        self.n_parallel = n_parallel
        self.eid = kwargs.get("eid", None)
        self.result_labels = kwargs.get('multi_res_labels', None)

        self.track_intermediate_results = kwargs.get("track_intermediate_results", False)
        self.interm_job_res = None
        if self.track_intermediate_results:
            self.interm_job_res = dict()

        # variables for early stop impl
        if "early_stop" in kwargs:
            self.policy = kwargs["early_stop"]["aup_policy"]
            self.policy_steps = kwargs["early_stop"]["aup_policy_steps"]
            self.warmup = kwargs["early_stop"].get("warmup", 0)
            self.bandit_factor = kwargs["early_stop"].get("bandit_factor", 0.5)
            self.truncation_percentage = kwargs["early_stop"].get("truncation_percentage", 0.3)
            self.curve_fitting_threshold = kwargs["early_stop"].get("curve_fitting_threshold", 0.95)
            self.curve_fitting_max_iters = kwargs["early_stop"].get("curve_fitting_max_iters", None)
            self.curve_fitting_timeout = kwargs["early_stop"].get("curve_fitting_timeout", 60)
            self.job_checked = dict()
            self.early_stop_daemon_finished = False
            self.stopped_jobs = set()
            if self.policy == "curve_fitting" and self.curve_fitting_max_iters is None:
                raise ValueError("Curve fitting policy requires argument \"curve_fitting_max_iters\" representing " +
                                 "the total number of intermediate results that the script will provide.")
            self.early_stop_daemon = threading.Thread(target=AbstractResourceManager.early_stop_daemon_fun,
                                        args=(self,), daemon=True)
            self.early_stop_daemon.start()
        else:
            self.warmup = None
            self.policy = None
            self.policy_steps = 0
            self.job_checked = dict()
            self.early_stop_daemon_finished = True
            self.early_stop_daemon = None
            self.stopped_jobs = None

    def finish(self, status="FINISHED"):
        """
        Finish up the resource allocation.
        :param status: status of the experiment
        :type status: string

        :return: Max/Min result in experiment (job id, score)
        :rtype: None | [int, float]
        """
        self.connector.end_experiment(self.eid, status)
        if self.early_stop_daemon != None:
            self.early_stop_daemon_finished = True
            self.early_stop_daemon.join()
        return self.connector.get_best_result(self.eid, maximize=self.maximize)

    def finish_job(self, jid, score, status=None):
        """
        Finish one job

        :param jid: job ID
        :type jid: int
        :param score: job for the experiment
        :type score: float | None
        """
        if jid in self.jobs:
            rid = self.jobs.pop(jid)
            self.connector.job_finished(rid, jid, score, status)
        else:
            logger.warning("Job %d finished after job suspension, result may lose" % jid)

    def get_available(self, username, rtype, rid_blacklist=None):
        """
        method to get the available resource to run a job

        :param username: username for job running
        :type username: str
        :param rtype: resource type
        :type rtype: str
        :param rid_blacklist: resource ids to ignore
        :type rid_blacklist: [int]
        :return: a random selection of all available resource IDs
        :rtype: int
        """
        rids = self.connector.get_available_resource(username, rtype, rid_blacklist)
        logger.debug("Request resource (%s) for user %s and get %s" % (rtype, username, rids.__str__()))
        return random.choice(rids) if rids else None

    def run_job(self, job, rid, exp_config, call_back_func, **kwargs):
        """
        Job running interface, this is called by :mod:`aup.EE.Experiment`.

        It is a wrapper for :func:`run`.

        :param job: Job to run
        :type job: Job
        :param rid: resource ID
        :type rid: int
        :param exp_config: experiment configuration
        :type exp_config: BasicConfig
        :param call_back_func: call back function to update result
        :type call_back_func: function object
        """
        self.connector.take_available_resource(rid)
        self.jobs[job.jid] = rid

        if self.interm_job_res != None:
            self.interm_job_res[job.jid] = list()
            self.job_checked[job.jid] = list()

        try:
            self.run(job, rid, exp_config, call_back_func, **kwargs)
        except EnvironmentError as e:
            self.connector.free_used_resource(rid)
            logger.fatal("Experiment interrupted.")
            raise(e)

    def append_interm_res(self, jid, interm_res):
        if self.interm_job_res == None:
            return None

        if jid in self.interm_job_res:
            self.interm_job_res[jid].append(interm_res)
            if self.connector:
                return self.connector.save_intermediate_result(jid, interm_res)
            else:
                logger.warning("Could not save intermediate result: no connector attached to resource manager")
            return None
        else:
            logger.fatal("Job {} should have already started!".format(jid))
            return None

    def append_multiple_results(self, jid, irid, eid, scores):
        if self.result_labels is None or len(scores) == 0:
            return

        assert len(self.result_labels) == len(scores), \
                "labels size mismatch with the provided scores"

        if self.connector is not None:
            self.connector.save_multiple_results(jid, irid, eid, self.result_labels, scores)

    def set_last_multiple_results(self, eid, jid):
        if self.result_labels is None:
            return

        if self.connector is not None:
            self.connector.set_last_multiple_results(eid, jid, len(self.result_labels))

    def stop_job(self, jid):
        """
        Stop a job for early stopping strategies

        :param jid: job ID
        :type jid: int
        """
        if jid not in self.jobs:
            logger.debug("Tried to stop job {} not in currently running jobs.".format(jid))
        with self.stopped_jobs_lock:
            self.stopped_jobs.add(jid)

    def is_job_stopped(self, jid):
        """
        Returns whether or not a specific job stop is pending

        :param jid: job ID
        :type jid: int
        :return: whether or not the given job ID is in the list of pending job stops
        :rtype: bool
        """
        with self.stopped_jobs_lock:
            return self.stopped_jobs is not None and jid in self.stopped_jobs

    @abc.abstractmethod
    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        """
        Job running implemented for the specific resource manager. 
        It is called by :func:`run_job`.

        :param job: a job object
        :type job: Job
        :param rid: resource id returned from :func:`get_available`.
        :type rid: int
        :param exp_config: experiment configuration
        :type exp_config: BasicConfig
        :param call_back_func: function to trigger after job finished
        :type call_back_func: function object
        """
        raise NotImplementedError

    def suspend(self):
        """
        Suspend job upon request
        """
        for jid in list(self.jobs.keys()):
            self.finish_job(jid, None)
            logger.warning("Job %d is canceled" % jid)

    def run_curve_fitting(self, interm_res, c_jid, step, comp_fn, curve_fitting_threshold, best_val):
        curvemodel = CurveModel(self.curve_fitting_max_iters)
        predict_y = curvemodel.predict(interm_res, timeout=self.curve_fitting_timeout)
        if predict_y is None:
            return
        if not comp_fn(predict_y, curve_fitting_threshold * best_val):
            if self.is_job_stopped(c_jid):
                return
            self.stop_job(c_jid)
            logger.info("Stopping job {} early (step {}): predicted end value {:.4f} is lower than the best value so far {:.4f} within the given {:.2f}% threshold (={:.4f})".format(
                c_jid, step, predict_y, best_val, 100. * curve_fitting_threshold, curve_fitting_threshold * best_val))

    def early_stop_daemon_fun(self):
        while not self.early_stop_daemon_finished:
            # do not consider the early stopped jobs
            with self.stopped_jobs_lock:
                current_jobs = set(self.jobs) - self.stopped_jobs

            finished_interm_job_res = self.connector.get_intermediate_results_experiment(self.eid, "FINISHED")
            current_interm_job_res = self.connector.get_intermediate_results_jobs(list(current_jobs))
            interm_job_res = {**current_interm_job_res, **finished_interm_job_res}

            best_fn = np.max if self.maximize else np.min
            comp_fn = (lambda x, target: x >= target) if self.maximize else \
                      (lambda x, target: x <= target)

            curve_fitting_threads = []

            for c_jid, c_interm_res in current_interm_job_res.items():
                if len(c_interm_res) < self.warmup:
                    continue

                if c_jid not in self.job_checked:
                    self.job_checked[c_jid] = []

                k = len(c_interm_res) // self.policy_steps
                if k < 1:
                    time.sleep(EARLY_STOPPING_SLEEP)
                    continue

                step = k * self.policy_steps
                if step in self.job_checked[c_jid]: # job already compared up until this step, waiting for next k multiple
                    time.sleep(EARLY_STOPPING_SLEEP)
                    continue

                comp_interm_job_res = {jid: vals for jid, vals in interm_job_res.items() if len(vals) >= step and jid != c_jid}
                if len(comp_interm_job_res) < 1: # too few jobs 
                    time.sleep(EARLY_STOPPING_SLEEP)
                    continue

                if self.policy == "median":
                    avgs = [np.average(vals[:step]) for vals in comp_interm_job_res.values()]
                    median = np.median(avgs)
                    best_val = np.average(c_interm_res[:step])
                    if not comp_fn(best_val, median):
                        self.stop_job(c_jid)
                        logger.info("Stopping job {} early (step {}): best value so far {:.4f} worse than median of averages {:.4f} for {} other jobs".format(
                            c_jid, step, best_val, median, len(comp_interm_job_res)))
                elif self.policy == "bandit":
                    bandit_best_val = best_fn([best_fn(vals[:step]) for vals in comp_interm_job_res.values()])
                    best_val = best_fn(c_interm_res[:step])
                    bandit_factor = self.bandit_factor if ((self.maximize and np.sign(bandit_best_val) == 1) or (not self.maximize and np.sign(bandit_best_val) == -1)) else \
                                    2 - self.bandit_factor
                    if not comp_fn(best_val, bandit_factor * bandit_best_val):
                        self.stop_job(c_jid)
                        logger.info("Stopping job {} early (step {}): best value so far {:.4f} worse than a factor {:.4f} of best overall value {:.4f} (={:.4f}) for {} other jobs".format(
                            c_jid, step, best_val, bandit_factor, bandit_best_val, bandit_factor * bandit_best_val, len(comp_interm_job_res)))
                elif self.policy == "truncation":
                    best_vals = sorted([(jid, best_fn(vals[:step])) for jid, vals in (list(comp_interm_job_res.items()) + [(c_jid, c_interm_res)])], 
                                        key=lambda t: t[1], reverse=not self.maximize)
                    best_val_idx = next((idx for idx, (jid, val) in enumerate(best_vals) if jid == c_jid)) + 1
                    perc = float(best_val_idx) / len(best_vals)
                    if perc <= self.truncation_percentage:
                        self.stop_job(c_jid)
                        logger.info("Stopping job {} early (step {}): best value so far {:.4f} is in the bottom {:.2f}% of {} jobs, which is lower than the {:.2f}% cutoff".format(
                            c_jid, step, best_vals[best_val_idx-1][1], 100. * best_val_idx / len(best_vals), len(best_vals), 100. * self.truncation_percentage))
                elif self.policy == "curve_fitting":
                    if len(finished_interm_job_res) < 1 or step <= CURVE_FITTING_MIN_ITS:
                        continue
                    interm_res = copy.deepcopy(c_interm_res)
                    best_val = best_fn([best_fn(vals) for vals in finished_interm_job_res.values()])
                    if not self.maximize:
                        interm_res *= -1
                        best_val *= -1
                    curve_fitting_threshold = self.curve_fitting_threshold if np.sign(best_val) == 1 else \
                                              2 - self.curve_fitting_threshold
                    cf_thread = threading.Thread(target=self.run_curve_fitting, 
                        args=(interm_res[:step], c_jid, step, (lambda x, target: x >= target), curve_fitting_threshold, best_val))
                    cf_thread.start()
                    curve_fitting_threads += [cf_thread]

                self.job_checked[c_jid] += [step]
            
            for thread in curve_fitting_threads:
                thread.join()

            time.sleep(EARLY_STOPPING_SLEEP)

    def refresh(self):
        '''
        Method for refreshing timers/variables etc
        '''
        pass

    def log_error_message(self, msg):
        self.connector.log_error_message(self.eid, msg)
