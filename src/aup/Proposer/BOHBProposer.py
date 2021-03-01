"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.Proposer.BOHBProposer
=========================

BOBH proposer inherited from `HpBandSter <https://automl.github.io/HpBandSter/build/html/index.html>`_ to showcase
the simplicity of Auptimizer to integrate new HPO algorithms.  The `get_params()` method is based on the
`master.py <https://github.com/automl/HpBandSter/blob/master/hpbandster/core/master.py>`_ from the original BOHB implementation.

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

Detailed explanations availale on the `HpBandSter API documentation page
<https://automl.github.io/HpBandSter/build/html/optimizers/bohb.html>`_.

==================== =================== ========================================
Name                 Default value       Explanation
==================== =================== ========================================
n_iterations         4                   General iterations
min_points_in_model  None                Number of points to construct KDE
top_n_percent        15                  Percentage to keep
num_samples          64                  Number of samples for EI
random_fraction      0.3333333333333333  Fraction to explore randomly
bandwidth_factor     3                   Widening factor for KDE
min_bandwidth        0.001               Minimum sample bandwidth
==================== =================== ========================================


APIs
----
"""

import logging

import numpy as np
from six.moves import input
from six import PY3

from .AbstractProposer import AbstractProposer
from . import ProposerStatus
from ..utils import set_default_keyvalue
from .hpbandster.optimizers.bohb import BOHB
from .hpbandster.optimizers.iterations import SuccessiveHalving

import ConfigSpace as CS

from hpbandster.optimizers.config_generators.bohb import BOHB
from hpbandster.core.dispatcher import Job

logger = logging.getLogger(__name__)

assert PY3, "BOHB hpbandster supports Python 3 only!"

BOHB_DEFAULT = dict(min_points_in_model=None,
                    top_n_percent=15,
                    num_samples=64,
                    random_fraction=0.3333333333333333,
                    bandwidth_factor=3,
                    min_bandwidth=0.001)

SH_DEFAULT = dict(eta=3,
                  min_budget=0.01,
                  max_budget=1)


class BOHBProposer(AbstractProposer):
    def __init__(self, config):
        super(BOHBProposer, self).__init__(config)
        self.tid = 0
        self.target = 1 if config['target'] == min else -1  # bohb targets for loss only

        # BOHB config parameters
        set_default_keyvalue("n_iterations", 4, config)
        for k, v in BOHB_DEFAULT.items():
            set_default_keyvalue(k, v, config)
        if not config['min_points_in_model']:
            config['min_points_in_model'] = None
        # hyperband related parameters
        for k, v in SH_DEFAULT.items():
            set_default_keyvalue(k, v, config)
        # Hyperband related settings - modified from hpbandster/optimizers/bohb.py
        self.eta = config['eta']
        self.min_budget = config['min_budget']
        self.max_budget = config['max_budget']
        self.max_SH_iter = -int(np.log(self.min_budget / self.max_budget) / np.log(self.eta)) + 1
        self.budgets = self.max_budget * np.power(self.eta, -np.linspace(self.max_SH_iter - 1, 0, self.max_SH_iter))
        self.n_iterations = config['n_iterations']

        self.nSamples = self._get_nSample()
        bohb_config = {k: config[k] for k in BOHB_DEFAULT}
        configspace = self.create_configspace(config['parameter_config'])

        self.config_generator = BOHB(configspace, **bohb_config)

        ## Based on master.py
        self.iterations = []
        self.running_jobs = {}

    def get_param(self):
        """
        Get the next hyperparameter values, return None when experiment is finished.
        :return: hyperparameters in dictionary
        """
        while True:
            next_run = None
            for i in self.active_iterations():
                next_run = self.iterations[i].get_next_run()
                if next_run is not None:
                    break

            if next_run is not None:
                logger.debug("new hyperparameters %s" % (next_run,))
                break
            else:
                if self.n_iterations > 0:
                    logger.debug("create new iteration for %d" % self.n_iterations)
                    self.iterations.append(self.get_next_iteration(len(self.iterations)))
                    self.n_iterations -= 1
                else:
                    self.set_status(ProposerStatus.FINISHED)
                    return None

        config_id, config, budget = next_run
        job = Job(config_id, config=config, budget=budget)
        job.time_it("started")
        self.running_jobs[self.tid] = job
        config = config.copy()
        config['tid'] = self.tid
        config['n_iterations'] = budget  # for job execution
        self.tid += 1
        return config

    def update(self, score, job):
        """
        Wrap result and transfer to HpBandSter
        :param score: result
        :param job: job contains job id for configuration matching
        """
        i = job.config['tid']
        job = self.running_jobs[i]
        job.time_it("finished")
        job.result = {'loss': score * self.target}
        self.iterations[job.id[0]].register_result(job)
        self.config_generator.new_result(job)
        del self.running_jobs[i]

    def failed(self, job):
        """
        Failed jobs unsupported by BOHB Proposer.

        :param job: Failed job, containing job id
        :type job: Job
        """
        super().failed(job)
        raise NotImplementedError("BOHBProposer does not support failed jobs")

    def get_next_iteration(self, iteration, iteration_kwargs={}):
        """ Copied from https://github.com/automl/HpBandSter/blob/master/hpbandster/optimizers/bohb.py
        """
        s = self.max_SH_iter - 1 - (iteration % self.max_SH_iter)
        n0 = int(np.floor(self.max_SH_iter / (s + 1)) * self.eta ** s)
        ns = [max(int(n0 * (self.eta ** (-i))), 1) for i in range(s + 1)]
        return (SuccessiveHalving(HPB_iter=iteration, num_configs=ns, budgets=self.budgets[(-s - 1):],
                                  config_sampler=self.config_generator.get_config, **iteration_kwargs))

    def _get_nSample(self):
        nSamples = 0
        for iteration in range(self.n_iterations):
            s = self.max_SH_iter - 1 - (iteration % self.max_SH_iter)
            n0 = int(np.floor(self.max_SH_iter / (s + 1)) * self.eta ** s)
            ns = [max(int(n0 * (self.eta ** (-i))), 1) for i in range(s + 1)]
            nSamples += sum(ns)
        logger.debug("total exp %d:" % nSamples)
        return nSamples

    @staticmethod
    def create_configspace(parameter_config):
        """
        Wrap the Worker's get_configspace() function for HpBandSter interface
        """
        cs = CS.ConfigurationSpace()
        params = []
        for config in parameter_config:
            p = AbstractProposer.parse_param_config(config)
            if p['type'] == 'choice':
                param = CS.CategoricalHyperparameter(p['name'], choices=p['range'])
            else:  # for int or float
                param = dict(name=p['name'])
                param['lower'], param['upper'] = min(p['range']), max(p['range'])
                if p['type'] == 'int':
                    param = CS.UniformIntegerHyperparameter(**param)
                else:
                    param = CS.UniformFloatHyperparameter(**param)
            params.append(param)
        cs.add_hyperparameters(params)
        return cs

    @staticmethod
    def setup_config():  # pragma: no cover
        config = dict()
        for k, v in BOHB_DEFAULT.items():
            if k == "min_points_in_model":
                config[k] = input("%s [%s]:" % (k, v))
                if config[k]:
                    config[k] = int(config[k])
            else:
                config[k] = type(v)(input("%s [%s]:" % (k, v)) or v)
        for k, v in SH_DEFAULT.items():
            config[k] = type(v)(input("%s [%s]:" % (k, v)) or v)
        config.update(AbstractProposer.setup_config())
        return config

    def active_iterations(self):  # pragma: no cover
        """
        Based on :func:`hpbandster.core.master.Master.active_iterations`.
        """
        return list(filter(lambda idx: not self.iterations[idx].is_finished, range(len(self.iterations))))

    def save(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    def reload(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)