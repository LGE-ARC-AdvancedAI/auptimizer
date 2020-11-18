"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.Proposer.SequenceProposer
=============================

Sequence proposer of the parameters

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

============  ========================================
Name          Explanation
============  ========================================
proposer      sequence
============  ========================================

Specific parameters for ``parameter_config``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

========= ==========================================================================
Name      Explanation
========= ==========================================================================
name      name of the variable, will be used in the job config, i.e. training code
type      type of the parameter to be sampled: choose from "float","int","choice"
range     range of the parameter.  For "choice", list all the feasible values
interval  interval of sequence, default of 1 for int and float; overwrite n
n         number of samples for this variable, will compute interval; >=2
========= ==========================================================================

APIs
----
"""
import abc
import logging
from ast import literal_eval
from math import floor

from six.moves import reduce, input

from .AbstractProposer import AbstractProposer
from ..utils import check_missing_key, get_from_options

ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

logger = logging.getLogger(__name__)


# could add conditional proposer


class _AbstractGen(object):
    def __init__(self, conf):
        self.name = conf["name"]
        self.current = None
        self.len = 0

    @abc.abstractmethod
    def get(self, next_flag=True):  # pragma: no cover
        # next_flag is for retrieve the first element in the grid space.
        raise NotImplementedError

    @classmethod
    def get_gen(cls, conf):
        if conf['type'].lower() == "int":
            return _IntGen(conf)
        elif conf['type'].lower() == "float":
            return _FloatGen(conf)
        elif conf['type'].lower() == "choice":
            return _ChoiceGen(conf)
        else:
            msg = "Data type %s is not supported" % conf['type']
            logger.fatal(msg)
            raise KeyError(msg)


class _IntGen(_AbstractGen):
    def __init__(self, conf):
        super(_IntGen, self).__init__(conf)
        self.min, self.max = conf["range"]
        if "interval" in conf:
            self.interval = conf["interval"]
        elif "n" in conf:
            self.interval = floor((self.max - self.min) / (conf["n"] - 1))
        else:
            logger.warning("Using default interval of 1")
            self.interval = 1
        self.len = floor((self.max - self.min) / self.interval) + 1
        self.current = self.min

    def get(self, next_flag=True):
        if next_flag:
            val = self.current + self.interval
            if val > self.max:
                self.current = self.min
                return self.current, True
            else:
                self.current = val
                return self.current, False
        else:
            return self.current, False


class _FloatGen(_AbstractGen):
    def __init__(self, conf):
        super(_FloatGen, self).__init__(conf)
        self.min, self.max = conf["range"]
        if "interval" in conf:
            self.interval = conf["interval"]
        elif "n" in conf:
            self.interval = (self.max - self.min) / float(conf["n"] - 1)
        else:
            logger.warning("Using default interval of 1")
            self.interval = 1
        self.len = floor((self.max - self.min) / self.interval) + 1
        self.current = self.min
        self.max += self.interval*0.1 # avoid precision error for comparison.

    def get(self, next_flag=True):
        if next_flag:
            val = self.current + self.interval
            if val > self.max:  # loop back
                self.current = self.min
                return self.current, True
            else:
                self.current = val
                return self.current, False
        else:
            return self.current, False


class _ChoiceGen(_AbstractGen):
    def __init__(self, conf):
        super(_ChoiceGen, self).__init__(conf)
        self.range = conf["range"]
        self.len = len(self.range)
        self.current = 0

    def get(self, next_flag=True):
        if next_flag:
            self.current += 1
            if self.current < self.len:
                return self.range[self.current], False
            else:
                self.current = 0
                return self.range[self.current], True
        else:
            return self.range[self.current], False


class SequenceProposer(AbstractProposer):
    def __init__(self, config):
        super(SequenceProposer, self).__init__(config)
        self.params_gen = []
        for param in config["parameter_config"]:
            check_missing_key(param, "name",
                              "Missing name of the parameter, need to be consistent with your training code",
                              log=logger)
            p = super(SequenceProposer, self).parse_param_config(param)
            self.params_gen.append(_AbstractGen.get_gen(p))
        self.nSamples = reduce(lambda x, y: x * y, [i.len for i in self.params_gen])

    @staticmethod
    def setup_config():  # pragma: no cover
        config = []
        try:
            print("start adding hyperparameters, use 'stop' or ctrl+c to exit")
            while True:
                name = input("variable name:")
                if name == "stop":
                    break
                vrange = literal_eval("[" + input("range (separated by ,):") + "]")
                if len(vrange) == 0:
                    raise ValueError("range needs at least one element")
                vtype = get_from_options("type:", ("choice", "float", "int"))
                c = {'name': name, "range": vrange, "type": vtype}
                if vtype != "choice":
                    interval = input("interval for grid search, or skip to use total number for this variable:")
                    if not interval:
                        n = int(input("number of values for this variable [2]:") or 2)
                        if n < 2:
                            raise ValueError("number of values should be larger than 2, or use choice type")
                        c['n'] = n
                    else:
                        if vtype == 'float':
                            c['interval'] = float(interval)
                        else:
                            c['interval'] = int(interval)
                config.append(c)
        except KeyboardInterrupt:
            pass
        return {"parameter_config": config}

    def get_param(self, **kwargs):
        if self.counter == 0:
            self.current_proposal[self.params_gen[0].name], next_flag = self.params_gen[0].get(next_flag=False)
        else:
            self.current_proposal[self.params_gen[0].name], next_flag = self.params_gen[0].get(next_flag=True)
        for i in self.params_gen[1:]:
            self.current_proposal[i.name], next_flag = i.get(next_flag=next_flag)
        logger.debug(self.current_proposal)
        return self.current_proposal
