"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.Proposer.AbstractProposer
=============================

:mod:`aup.Proposer.AbstractProposer` provide interface for Hyperparameter Optimization Modules.

APIs
----
"""
import abc
import logging
import pickle
import json
import threading
from six.moves import input

from ..utils import set_default_keyvalue, check_missing_key, get_from_options
from . import ProposerStatus

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

logger = logging.getLogger(__name__)


def create_param_config(name, vrange, vtype):
    """
    Reads the configuration file and checks for errors.
    """
    if vtype not in ('float', 'int', 'choice'):
        raise ValueError("%s is not supported as hyperparameter type" % vtype)
    if vtype != 'choice' and len(vrange) != 2:
        raise ValueError("Range need to be a two element tuple for %s" % vtype)

    return {'name': name, 'range': vrange, 'type': vtype}

class AbstractProposer(ABC):
    """
    Proposer to generate new values for hyperparameters

    :param config: experiment configuration
    :type config: BasicConfig
    """

    def __init__(self, config):
        self.nSamples = 0   # number of total jobs for an experiment
        self.counter = 0    # number of executed jobs
        self.current_proposal = dict()
        self.status = ProposerStatus.RUNNING  # whether the experiment is finished
        self.status_lock = threading.Lock()
        AbstractProposer.verify_config(self, config)

    def set_status(self, status):
        with self.status_lock:
            self.status = status

    def get_status(self):
        with self.status_lock:
            return self.status

    def increment_job_counter(self):
        with self.status_lock:
            self.counter += 1

    def check_termination(self):
        with self.status_lock:
            if self.counter >= self.nSamples:
                self.status = ProposerStatus.FINISHED

    def get_remaining_jobs(self):
        with self.status_lock:
            return self.nSamples - self.counter

    @staticmethod
    def setup_config():  # pragma: no cover
        config = []
        try:
            print("start adding hyperparameters, use 'stop' for variable name or ctrl+c to exit")
            while True:
                name = input("variable name:")
                if name == "stop":
                    break
                try:
                    res = input("range (separated by ,):")
                    if "'" in res:
                        res = res.replace("'", '"')
                    if res[0] == '[' and res[-1] == ']':
                        vrange = json.loads(res)
                    else:
                        vrange = json.loads("[" + res + "]")
                except ValueError:
                    logger.critical("failed to parse range, treat it as strings separated by ','")
                    vrange = res.split(",")
                if len(vrange) == 0:
                    raise ValueError("range needs at least one element")
                vtype = get_from_options("type:", ("choice", "float", "int"))
                config.append({'name': name, "range": vrange, "type": vtype})
        except KeyboardInterrupt:
            print("Config interrupted, completed variables are saved.")
        return {"parameter_config": config}

    @staticmethod
    def parse_param_config(config):
        """
        Parse the given experiment configuration of ``parameter_config``
        If values are missing, fill in defaults.

        :param config: config["param_config"]
        :type config: dict
        :return: updated config
        :rtype: dict
        """
        check_missing_key(config, "name",
                          "Missing name of the parameter, need to be consistent with your training code",
                          log=logger)
        set_default_keyvalue("type", "int", config, log=logger)
        set_default_keyvalue("range", [0, 1], config, log=logger)
        return config

    def get(self, **kwargs):
        """
        Wrapper for specific :func:`get_param` to update ``current_proposal`` and ``counter``.

        :param kwargs: any arguments to be passed to :func:`get_param`
        :type kwargs: dict
        :return: parameter values
        :rtype: dict
        """
        self.check_termination()
        if self.get_status() != ProposerStatus.RUNNING:
            return None
        self.current_proposal = self.get_param(**kwargs)

        logger.debug(self.current_proposal)
        if not self.current_proposal:
            return None

        return self.current_proposal.copy()

    @abc.abstractmethod
    def get_param(self, **kwargs):
        """
        Get new proposed parameter values
        """
        raise NotImplementedError

    def reload(self, path):
        """
        Reload Proposer state from path

        :param path: path to reload
        :type path: str
        """
        logger.info("Reload %s, previous cancelled job won't be run", path)
        with open(path, 'rb') as f:
            d = pickle.load(f)
        for i in d.__dict__:
            self.__dict__[i] = d.__dict__[i]
        return self

    def reset(self):
        """
        Reset proposer
        """
        with self.status_lock:
            self.counter = 0
            self.status = ProposerStatus.RUNNING

    def save(self, path):
        """
        Save Proposer state to path.
        
        **Some proposer can not generate new parameters after saving.**

        :param path: path to save
        :type path: str
        """
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def update(self, score, job):
        """
        Update scores in proposer history

        :param score: score returned by Job
        :type score: float
        :param job: Finished job
        :type job: Job
        """
        logger.debug("Get score ({}) for job {}".format(score, job.jid))

    def failed(self, job):
        """
        Mark job as failed in proposer history.
        
        :param job: Failed job
        :type job: Job
        """
        logger.debug("Job {} marked as failed".format(job.jid))

    def verify_config(self, config):
        """
        Verify the input configuration is enough for the proposer

        :param config: Experiment configuration of ``parameter_config``
        :type config: dict
        :return: config
        :rtype: dict
        """
        check_missing_key(config, "parameter_config",
                          "Specify the parameter configuration `parameter_config` to be searched", log=logger)
        for i in config["parameter_config"]:
            check_missing_key(i, "name", "hyperparameter name is missing", log=logger)
        return config

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['status_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.status_lock = threading.Lock()

