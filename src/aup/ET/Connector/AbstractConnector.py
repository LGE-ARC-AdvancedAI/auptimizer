"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.ET.Connector.AbstractConnector
==================================

Define the basic interface between experiment tracking and executor engine.

Currently, SQLite is the only one implemented.

APIs
----
"""
import abc
import logging

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
logger = logging.getLogger(__name__)


class AbstractConnector(ABC):
    # ################ General Part #################
    @abc.abstractmethod
    def close(self):
        """
        Mark the connector as closed. A closed connector should not be used anymore.
        """
        pass

    @abc.abstractmethod
    def is_closed(self):
        """
        Return whether or not the connector is closed. A closed connector should not be used anymore.
        """
        return False

    # ################ Resource Related Part #################
    @abc.abstractmethod
    def free_used_resource(self, rid):
        """
        Mark resource as free (opposite to :func:take_available_resource)

        :param rid: Resource ID(s)
        :type rid: int
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_resource_type(self):
        """
        Get the resource type for a given user
        :return: list of resource types
        :rtype: list
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_available_resource(self, username, rtype):
        """
        Get available resource for a user and resource type.
        Currently there is no limitation/requirement for user

        :param username: username
        :type username: str
        :param rtype: Resource type
        :type rtype: str
        :return: Resource Id
        :rtype: list(int)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def take_available_resource(self, rid):
        """
        Mark resource as used

        TODO - currently where is prevention for async update, might not be relevant in the near future

        :param rid: Resource ID(s)
        :type rid: int
        :return: True/False
        """
        raise NotImplementedError

    # ################ Experiment Related Part ################
    @abc.abstractmethod
    def end_experiment(self, eid):
        """
        Mark experiment as finished

        :param eid: Experiment ID
        :type eid: int
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_best_result(self, eid, maximize=True):
        """
        Retrieve the best job id and score from the database for experiment eid

        :param eid: Experiment ID
        :type eid: int
        :param maximize: whether to choose max or min
        :type maximize: bool
        :return: Job ID, score
        :rtype: list(int, float)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_experiment(self, username, exp_config):
        """
        Create an Experiment and track it

        :param username: username
        :type username: str
        :param name: experiment name
        :type name: str
        :param exp_config: configuration of experiment
        :type exp_config: dict
        :return: experiment ID
        :rtype: int
        """
        raise NotImplementedError

    # ################ Job Related Part #######################
    @abc.abstractmethod
    def end_job(self, jid, score, status):
        """
        Mark a job ended

        :param jid: Job ID
        :type jid: int
        :param score: score of the Job
        :type score: str
        :param status: status of the Job
        :type status: enumeration
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_experiment(self, username=None):
        """
        Get all Experiment IDs

        :param username: to get experiments for a specific user
        :type username: str
        :return: Experiment IDs
        :rtype: list(int)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_history(self, eid):
        """
        Get full history of an Experiment

        :param eid: Experiment ID
        :type eid: int
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_running_job(self, eid):
        """
        Get running Job IDs

        :param eid: Experiment ID
        :type eid: int
        :return: list of Job IDs
        :rtype: list(int)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_job(self, eid, rid, job_config):
        """
        Start a job with job configuration and track it

        :param eid: Experiment ID
        :type eid: int
        :param rid: Resource ID
        :type rid: int
        :param job_config: Configuration for :class:`aup.EE.Job.Job`
        :type job_config: BasicConfig
        :return: Job ID (jid)
        :rtype: int
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_job_attempt(self, rid, jid):
        """
        Starts a job attempt for a given job, using the given resource

        :param rid: Resource ID
        :type rid: int
        :param jid: Job ID
        :type jid: int
        :return: Job Attempt ID (jaid)
        :rtype: int
        """
        raise NotImplementedError

    @abc.abstractmethod
    def end_job_attempt(self, jid):
        """
        Ends a job attempt, but not a job (leaving room for retries)

        :param id: Job ID
        :type id: int
        """
        raise NotImplementedError

    def update_job_status(self, jid, status):
        """
        Change a job's status

        :param jid: Job ID
        :type jid: int
        :param status: new status
        :type status: enumeration
        """
        raise NotImplementedError

    # ################ Job interface for Experiment ##############
    def job_finished(self, rid, jid, score=None, status=None):
        """
        Clean up Job when it is finished

        :param rid: Resource ID to be free
        :type rid: int
        :param jid: Job ID
        :type jid: int
        :param score: score returned by Job (error case will be ERROR)
        :type score: float / str
        :param status: job status
        :type status: enumeration
        """
        logger.debug("Job %d is finished on %d, score is %s" % (jid, rid, score))
        self.free_used_resource(rid)
        self.end_job_attempt(jid)
        self.end_job(jid, score, status)

    def job_started(self, eid, rid, job_config):
        """
        Interface to automatically take resource and run job.

        :param eid: Experiment ID
        :type eid: int
        :param rid: Resource ID
        :type rid: int
        :param job_config: Configuration for Job
        :type job_config: BasicConfig
        :return: Job ID
        :rtype: int
        """
        self.take_available_resource(rid)
        return self.start_job(eid, rid, job_config)

    def job_failed(self, rid, jid):
        """
        Interface to take care of job failure in case of possible retries
        
        :param rid: Resource ID
        :type rid: int
        :param jid: Job ID
        :type jid: int
        """
        self.free_used_resource(rid)
        self.end_job_attempt(jid)
    
    def job_retry(self, rid, jid):
        """
        Interface to mark the beginning of a job retry

        :param rid: Resource ID
        :type rid: int
        :param jid: Job ID
        :type jid: int
        """
        self.take_available_resource(rid)
        return self.start_job_attempt(rid, jid)

    def save_intermediate_result(self, jid, score):
        """
        Interface for saving intermediate result for a job.

        :param jid: Job ID
        :type jid: int
        :param score: the intermediate result
        :type score: float
        :return: intermediate_result table id
        :rtype: int
        """
        raise NotImplementedError

    def get_intermediate_results_job(self, jid):
        """
        Interface for extracting all intermediate results available for a given job.

        :param jid: Job ID
        :type jid: int
        :return: list of intermediate results, in order
        :rtype: float list
        """
        raise NotImplementedError

    def get_intermediate_results_jobs(self, jids):
        """
        Interface for extracting all intermediate results available for a given list of jobs.

        :param jids: Job IDs
        :type jids: int list
        :return: dictionary mapping job IDs to lists of intermediate results, in order
        :rtype: dict<int, float list>
        """
        raise NotImplementedError

    def get_intermediate_results_experiment(self, eid, status):
        """
        Interface for extracting all intermediate results for all jobs of a given experiment, 
        fitting a given status.

        :param eid: Experiment ID
        :type eid: int
        :param status: Desired status for filtering jobs
        :type status: enumeration
        :return: dictionary mapping job IDs to lists of intermediate results, in order
        :rtype: dict<int, float list>
        """
        raise NotImplementedError

    def create_experiment(self, username, exp_config):
        """
        Interface for creating an experiment without starting it
        """
        raise NotImplementedError

    def delete_experiment(self, eid):
        """
        Interface for deleting an experiment by eid
        """
        raise NotImplementedError

    def get_experiment_status(self, eid):
        """
        Interface for getting the database status of an experiment
        """
        raise NotImplementedError

    def start_experiment_by_eid(self, eid):
        """
        Interface for (re)starting an experiment by eid
        """
        raise NotImplementedError

    def log_error_message(self, eid, msg):
        """
        Log in database the error message
        """
        raise NotImplementedError

    def save_multiple_results(self, jid, irid, eid, labels, scores):
        """
        Save in database other results desired by user
        """
        raise NotImplementedError

    def set_last_multiple_results(self, eid, jid, num_labels):
        """
        Set the 'is_last_result' flag to true for this jid
        """
        raise NotImplementedError
