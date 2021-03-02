"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.Proposer.RandomProposer
===========================

Random sampling of the parameters

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

============ ============= ========================================
Name         Default value Explanation
============ ============= ========================================
proposer     -             random
n_samples    -             Total number of trials to sample
random_seed  0             [Optional] seed for random generator
============ ============= ========================================

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
import logging

from numpy import random
from six.moves import input

from .AbstractProposer import AbstractProposer
from ..utils import check_missing_key, set_default_keyvalue

logger = logging.getLogger(__name__)


def _random_int(x):
    if len(x) != 2:
        msg = ("Range of random integer should have two elements, got %d" % len(x))
        logger.fatal(msg)
        raise ValueError(msg)
    return lambda: random.randint(x[0], x[1] + 1)


def _random_float(x):
    if len(x) != 2:
        msg = ("Range of random float should have two elements, got %d" % len(x))
        logger.fatal(msg)
        raise ValueError(msg)
    return lambda: random.rand() * (x[1] - x[0]) + x[0]


def _random_choice(x):
    if len(x) < 1:
        msg = "Range of random choice should have some elements, got nothing"
        logger.fatal(msg)
        raise ValueError(msg)
    return lambda: x[random.choice(len(x))]


_random_fun = {
    'int': _random_int,
    'float': _random_float,
    'choice': _random_choice
}


class RandomProposer(AbstractProposer):
    """
    Random proposer

    :param config: experiment configuration contains the details searching space
    :param random_seed: default random seed if not in config
    """

    def __init__(self, config, random_seed=0):
        super(RandomProposer, self).__init__(config)
        self.verify_config(config)
        self.nSamples = config["n_samples"]
        set_default_keyvalue("random_seed", random_seed, config, log=logger)
        random.seed(config["random_seed"])
        self.random_state = None  # for suspend and resume
        self.params_gen = {}
        for param in config["parameter_config"]:
            p = self.parse_param_config(param)
            self.params_gen[p['name']] = _random_fun[p['type']](p['range'])

    @staticmethod
    def setup_config():  # pragma: no cover
        """
        Set up experiment configuration
        :return: experiment config in dict.
        """
        config = dict()
        config['n_samples'] = int(input("number of model samples to draw randomly, `n_samples`, [1]:") or 1)
        config['random_seed'] = int(input("random seed, `random_seed`, [0]:") or 0)
        config.update(AbstractProposer.setup_config())
        return config

    def get_param(self, **kwargs):
        """
        Get the next parameter set
        :return: parameter name and value pairs in dict
        """
        if 'params_gen' not in self.__dict__:
            return None

        for i in self.params_gen:
            self.current_proposal[i] = self.params_gen[i]()
        logger.debug(self.current_proposal)
        return self.current_proposal

    def reload(self, path):
        super(RandomProposer, self).reload(path)
        random.set_state(self.random_state)
        self.random_state = None
        return self

    def save(self, path):
        if 'params_gen' in self.__dict__:
            del self.params_gen
        self.random_state = random.get_state()
        super(RandomProposer, self).save(path)

    def verify_config(self, config):
        check_missing_key(config, "n_samples", "Specify number of samples to randomly draw", log=logger)
        return config
