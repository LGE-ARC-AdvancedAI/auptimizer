"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Auptimizer client side functions
================================

This file can be copied to a remote machine instead of installing the whole Auptimizer package for job execution.

APIs
----
"""
from __future__ import print_function

import logging
import json
import pickle
import sys

logger = logging.getLogger("aup-minimal")

# supported data loading format
_SUPPORT_FORMAT = ("pkl", "json")


def print_result(result):
    """Function to print the result for :func:`parse_result`.
    This function should be the last line of your training code

    :param result: result from training code
    :type result: str
    """
    if result is list:
        result = ','.join([str(r) for r in result])
    else:
        result = str(result).lstrip()  # avoid line break
    print("\n#Auptimizer:%s" % result, file=sys.stderr)


class BasicConfig(dict):
    """
    User-friendly :class:`dict` supports:

    * load and save for json/pickle format (.json/.pkl)
    * easy key/value access as config.key or config["key"]
    * compatible with :class:`dict`

    :param kwargs: key-value pairs to initialize the configuration
    :type kwargs: dict
    """
    def load(self, filename):
        """Load config parameters from JSON/pickle file

        :param filename: file name ends with [.json|.pkl]
        :type filename: string
        :return: configuration parsed from file
        :rtype: aup.BasicConfig
        """
        name = "_load_" + BasicConfig._get_format(filename)
        func = getattr(self, name)
        data = func(filename)
        if type(data) is not dict:
            raise TypeError("Config must be dict")
        self.update(data)
        logger.debug("Load config from %s: %s" % (filename, data.__str__()))
        return self

    def save(self, filename):
        """
        Save configuration as dict in JSON/pickle

        :param filename: file name ends with [.json|.pkl]
        :type filename: string
        """
        name = "_save_" + BasicConfig._get_format(filename)
        func = getattr(self, name)
        func(filename)
        logger.debug("Config saved to %s" % filename)

    @staticmethod
    def _get_format(filename):
        name = filename.split(".")[-1].lower()
        if name not in _SUPPORT_FORMAT:
            raise ValueError("Un-support file format, choose from %s." % ",".join(_SUPPORT_FORMAT))
        return name

    @staticmethod
    def _load_json(filename):
        with open(filename, 'r') as f:
            return json.load(f)

    @staticmethod
    def _load_pkl(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)

    def _save_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self, f)

    def _save_pkl(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(dict(self), f)

    @staticmethod
    def save_flags(filename):
        """
        Save tf flags for reuse - not used, not tested

        :param filename: output file
        """
        from absl import flags
        logger.info("Write flags into %s")
        with open(filename, 'w') as f:
            f.write(flags.FLAGS.flags_into_string())

    def to_flags(self, FLAGS):
        """
        Update values in FLAGS from BasicConfig

        :param FLAGS: tensorflow/absl FLAGS
        """
        for i in FLAGS:
            if i in self:
                logger.debug("set %s in FLAGS" % i)
                setattr(FLAGS, i, self[i])
            else:
                logger.debug("Use default %s" % i)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __delattr__(self, key):
        self.__delitem__(key)

    def __hash__(self):
        return super(BasicConfig, self).__hash__()
