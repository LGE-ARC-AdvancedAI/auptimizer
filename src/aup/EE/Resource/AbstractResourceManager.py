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
import importlib
import logging
import random

from ...utils import DEFAULT_AUPTIMIZER_PATH

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
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

    def __init__(self, connector, *args, **kwargs):
        self.connector = connector
        self.jobs = dict()

    def finish(self, eid, maximize=True):
        """
        Finish up the resource allocation.

        :param eid: Experiment ID
        :type eid: int
        :param maximize: Report Max or Min of resources
        :type maximize: bool
        :return: Max/Min result in experiment (job id, score)
        :rtype: None | [int, float]
        """
        self.connector.end_experiment(eid)
        return self.connector.get_best_result(eid, maximize=maximize)

    def finish_job(self, jid, score):
        """
        Finish one job

        :param jid: job ID
        :type jid: int
        :param score: job for the experiment
        :type score: float | None
        """
        if jid in self.jobs:
            rid = self.jobs.pop(jid)
            self.connector.job_finished(rid, jid, score)
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
        try:
            self.run(job, rid, exp_config, call_back_func, **kwargs)
        except EnvironmentError as e:
            self.connector.free_used_resource(rid)
            logger.fatal("Experiment interrupted.")
            raise(e)

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
