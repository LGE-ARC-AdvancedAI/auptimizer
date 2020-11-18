"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
  
aup.Proposer.HyperoptProposer
=============================


This is converted from `Hyperopt repo commit 762e89f <https://github.com/hyperopt/hyperopt>`_

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~
============= ============== ========================================
Name          Default value  Explanation
============= ============== ========================================
proposer      -              hyperopt
random_seed   0              [Optional] seed for random generator
engine        tpe            engine to generate configurations for HyperOpt
n_samples     -              max_evals in hyperopt
============= ============== ========================================

Specific parameters for ``parameter_config``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

======= ==========================================================================
Name    Explanation
======= ==========================================================================
name    name of the variable, will be used in the job config, i.e. training code
type    type of the parameter to be sampled: choose from "float","int","choice"
range   range of the parameter.  For "choice", list all the feasible values
======= ==========================================================================

APIs
----
"""
import importlib
import logging

import numpy as np
from six.moves import input

from .AbstractProposer import AbstractProposer
from .hyperopt import hp, base
from .hyperopt.utils import coarse_utcnow
from ..utils import set_default_keyvalue, check_missing_key, get_from_options

logger = logging.getLogger(__name__)


def _get_algo(engine):
    module = importlib.import_module(".hyperopt.%s" % engine, "aup.Proposer")
    return module.suggest


def _convert(param_config):
    d = {}
    for param in param_config:
        if param['type'] == 'int':
            d[param['name']] = hp.randint(param['name'], param['range'][1] - param['range'][0])
            # hyperopt doesn't support [low, high] for int
        elif param['type'] == 'float':
            if len(param['range']) != 2:
                raise ValueError("HyperOpt: range for float only has two numbers, you have %d"%len(param['range']))
            param['range'] = sorted(param['range'])
            d[param['name']] = hp.uniform(param['name'], param['range'][0], param['range'][1])
        elif param['type'] == 'choice':
            d[param['name']] = hp.choice(param['name'], param['range'])
        else:
            msg = "%s is not supported type, choose int, float, choice" % param['type']
            logger.fatal(msg)
            raise KeyError(msg)
    return d


class HyperoptProposer(AbstractProposer):

    def __init__(self, config, random_seed=0):
        super(HyperoptProposer, self).__init__(config)

        set_default_keyvalue("engine", "tpe", config, log=logger)
        set_default_keyvalue("random_seed", random_seed, config, log=logger)

        self.target = -1 if config["target"] == "max" else 1  # default is to minimize
        self.verify_config(config)
        self.nSamples = config["n_samples"]
        self.parameter_config = config["parameter_config"]
        self.space = _convert(self.parameter_config)
        self.rstate = np.random.RandomState(config["random_seed"])
        self.domain = base.Domain(lambda x: logger.fatal("should not be run"), self.space)
        self.trials = base.Trials()
        self.algo = _get_algo(config["engine"])

    @staticmethod
    def setup_config():  # pragma: no cover
        config = dict()
        config['n_samples'] = int(input("number of model samples, `n_samples`, [1]:") or 1)
        config['random_seed'] = int(input("random seed, `random_seed`, [0]:") or 0)
        config['engine'] = get_from_options("search engine, `engine`", ['tpe', 'random'])
        config.update(AbstractProposer.setup_config())
        return config

    def get_param(self, **kwargs):
        """
        Restructure of hyperopt.fmin `run()`, `serial_evaluate()`.
        """
        new_ids = self.trials.new_trial_ids(1)  # only one config each time
        trial = self.algo(new_ids, self.domain, self.trials, self.rstate.randint(2 ** 31 - 1))[0]

        trial['state'] = base.JOB_STATE_RUNNING
        now = coarse_utcnow()
        trial['book_time'] = now
        trial['refresh_time'] = now
        spec = base.spec_from_misc(trial['misc'])

        self.trials.insert_trial_docs([trial])
        self.trials.refresh()

        for param in self.parameter_config:
            if param['type'] == "int":
                spec[param['name']] = int(spec[param['name']] + param['range'][0])
            if param['type'] == "choice":
                spec[param['name']] = param['range'][spec[param['name']]]
        spec['tid'] = trial['tid']
        return spec

    def reload(self, path):
        super(HyperoptProposer, self).reload(path)
        self.domain = base.Domain(lambda x: logger.fatal("should not be run"), self.space)

    def save(self, path):
        del self.domain
        super(HyperoptProposer, self).save(path)

    def update(self, score, job):
        """
        Restructure of hyperopt.fmin `serial_evaluation`.
        
        :param score: score returned from the training script
        :param job: job object contains tid for hyperopt internal update
        """
        super(HyperoptProposer, self).update(score, job)
        tid = job.config['tid']
        if score is not None:
            result = {'loss': score * self.target, 'status': 'ok'}
            state = base.JOB_STATE_DONE
        else:
            result = {'loss': None, 'status': 'fail'}
            state = base.JOB_STATE_ERROR
        for trial in self.trials._dynamic_trials:
            if tid == trial['tid']:
                trial['state'] = state
                trial['result'] = result
                trial['refresh_time'] = coarse_utcnow()
                self.trials.refresh()
                return
        msg = "Failed to locate job tid=%d" % tid
        logger.fatal(msg)
        raise KeyError(msg)

    def failed(self, job):
        """
        Failed jobs unsupported by Hyperopt Proposer.

        :param job: Failed job, containing job id
        :type job: Job
        """
        super(HyperoptProposer, self).failed(job)
        self.update(None, job)

    def verify_config(self, config):
        check_missing_key(config, "n_samples", "Specify number of samples to randomly draw", log=logger)
        for param in config["parameter_config"]:
            if "tid" in param["name"]:
                msg = "Parameter `tid` is conflict with hyperopt internal control parameter, please change the name"
                logger.fatal(msg)
                raise KeyError(msg)
        return config
