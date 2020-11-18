"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
  
aup.Proposer.HyperbandProposer
==============================

The code is based on `hyperband github commit a632209 <https://github.com/zygmuntz/hyperband>`_.

See `license <https://github.com/zygmuntz/hyperband/blob/master/LICENSE>`_ for redistribution.

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

============= ============== ========================================
Name          Default value  Explanation
============= ============== ========================================
proposer      -              hyperband
random_seed   0              [Optional] seed for random generator
max_iter      81             Max iterations (e.g. epochs) per configuration
eta           3              downsampling rate, choose 3 for training from scratch
skip_last     0              whether skip last element
engine        random         engine to generate configurations for hyperband
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


In the returned job_config, it has ``n_iterations`` and ``tid`` for tracking the HPO process.
``n_iterations`` marks how much resource should be allocated for this round of training (e.g. epochs);
``tid`` is used to recover the previous trained model if needed (i.e. finetune)

APIs
----
"""
import logging
import random
from math import log, ceil

from six.moves import input

from aup.Proposer import get_proposer
from .AbstractProposer import AbstractProposer
from ..utils import set_default_keyvalue, get_from_options

logger = logging.getLogger(__name__)


class HyperbandProposer(AbstractProposer):
    def __init__(self, config):
        super(HyperbandProposer, self).__init__(config)
        self.verify_config(config)
        self.target = -1 if config["target"] == "max" else 1
        self.max_iter = config["max_iter"]
        self.eta = config["eta"]
        self.skip_last = config["skip_last"]
        self.s_max = int(log(self.max_iter)/log(self.eta))
        self.B = (self.s_max+1)*self.max_iter

        self.results = []

        self.best_counter = -1
        self.s = self.s_max+1
        self.config = config

        self.nSamples = 0
        for s in reversed(range(self.s_max + 1)):
            self.nSamples += int(ceil(self.B / self.max_iter / (s + 1) * self.eta ** s))
        logger.info("Total number of samples is %d"%self.nSamples)
        set_default_keyvalue("random_seed", 0, config)
        random.seed(config["random_seed"])
        self.t = 0
        self.i = 0
        self.n = 0
        self.test_set = []
        self.r = 0
        self.n_configs = 0
        self.n_iterations = 0
        self.scores = {}
        self.setup(self.s_max)

    def setup(self, s):
        # Follow the hyperband paper, set up internal variables based on s_max
        self.s = s
        self.n = int(ceil(self.B / self.max_iter / (s + 1) * self.eta ** s))
        self.r = self.max_iter * self.eta ** (-s)
        gen_config = self.config.copy()
        gen_config["n_samples"] = self.n
        gen_config["random_seed"] = random.randint(0, 100)
        gen_config["proposer"] = gen_config["engine"]
        proposer = get_proposer(gen_config['proposer'])(gen_config)
        self.test_set = [proposer.get for _ in range(self.n)]
        self.t = 0
        self.i = 0
        self.n_configs = self.n * self.eta ** (-self.i)
        self.n_iterations = self.r * self.eta ** self.i

    def verify_config(self, config):
        for i in config["parameter_config"]:
            if i['name'] == "tid":
                msg = "`tid` is reserved for Hyperband"
                logger.fatal(msg)
                raise KeyError(msg)
        set_default_keyvalue("max_iter", 81, config, log=logger)
        set_default_keyvalue("eta", 3, config, log=logger)
        set_default_keyvalue("skip_last", 0, config, log=logger)
        set_default_keyvalue("engine", "random", config, log=logger)

    def get_param(self):
        if self.t == len(self.test_set):
            if len(self.scores) != self.t:
                self.current_proposal = None
                return None
            tids = sorted(self.scores, key=self.scores.get)
            tids = tids[0:int(self.n_configs / self.eta)]
            self.test_set = [self.test_set[i] for i in tids]
            self.scores = {}
            self.i += 1
            self.t = 0
            self.n_configs = self.n * self.eta ** (-self.i)
            self.n_iterations = self.r * self.eta ** self.i

        if self.i == (self.s+1-int(self.skip_last)):
            self.i = 0
            self.setup(self.s-1)
            logger.debug("\n*** {} configurations x {:.1f} iterations each".format(
                self.n_configs, self.n_iterations))

        if type(self.test_set[self.t]) != dict:
            self.test_set[self.t] = self.test_set[self.t]()
        self.test_set[self.t]['tid'] = self.t
        self.test_set[self.t]["n_iterations"] = self.n_iterations

        self.t += 1
        return self.test_set[self.t-1]  # return parameter configuration

    def update(self, score, job):
        self.scores[job.config["tid"]] = score * self.target

    def failed(self, job):
        super(HyperbandProposer, self).failed(job)
        raise NotImplementedError("HyperbandProposer does not support failed jobs")

    def save(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    def reload(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    @staticmethod
    def setup_config():  # pragma: no cover
        config = dict()
        config['max_iter'] = int(input("max iteration [81]:") or 81)
        config['eta'] = int(input("ita [3]") or 3)
        config["skip_last"] = int(input("skip last [0]") or '0')
        config["engine"] = get_from_options("Hyperparameter sampling engine", ["random", "sequence"])
        config.update(get_proposer(config['engine']).setup_config())
        return config
