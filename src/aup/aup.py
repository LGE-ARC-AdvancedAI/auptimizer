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
import inspect
import functools
import os
import shutil

logger = logging.getLogger("aup-minimal")

# supported data loading format
_SUPPORT_FORMAT = ("pkl", "json")

global user_callback_fn
global user_args
global user_kwargs

user_callback_fn = None
user_args = []
user_kwargs = {}

def print_result(result):
    """Function to print the result for :func:`parse_result`.
    This function should be the last line of your training code

    :param result: result from training code
    :type result: str
    """
    if type(result) is list:
        result = ','.join([str(r) for r in result])
    else:
        result = str(result).lstrip()  # avoid line break
    # force flush to get intermediate results in real time
    print("\n#Auptimizer:%s" % result, file=sys.stderr, flush=True)


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
                logger.debug("set %s in FLAGS", i)
                setattr(FLAGS, i, self[i])
            else:
                logger.debug("Use default %s", i)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __delattr__(self, key):
        self.__delitem__(key)

    def __hash__(self):
        return super(BasicConfig, self).__hash__()


def aup_args(func):
    """Decorator to wrap optimization target function `func`.
    
    Arguments:
        func {function} -- A function computes optimization target with specified hyperparameters
    """
    @functools.wraps(func)
    def wrapper(filename, **kwargs):
        """wrapper function
        
        Arguments:
            filename {str} -- configuration file
            kwargs {dict} -- additional arguments will overwrite existing configuration value
        Raises:
            ValueError: if a parameter is not assigned in config
        """
        # get current frame stack
        frm = inspect.stack()[1]
        # get module from stack
        mod = inspect.getmodule(frm[0])
        # get functions that contain "init" in name and call them
        functions_list = inspect.getmembers(sys.modules[mod.__name__], inspect.isfunction)
        functions_list = sorted(list(filter(lambda x: "init" in x[0], functions_list)))

        config = BasicConfig().load(filename)
        if kwargs:
            logger.critical("Overwritting config values from script, be cautious!")
            config.update(kwargs)

        for f in functions_list:
            f[1](**config)

        parameters = inspect.signature(func).parameters
        for p in parameters.items():
            if p[0] not in config:
                if p[1].default is inspect.Parameter.empty:
                    raise ValueError("`%s` is required in `%s()` but is not assigned in config file %s" % 
                                     (p[0], func.__name__, filename))
                logger.info("Using default value for %s", p[0])
        run_config = dict()
        for p in config:
            if p in parameters:
                run_config[p] = config[p]
            else:
                logger.warning("%s is not used in optimization"%p)

        val = func(**run_config)
        print_result(val)

        save_model = config.get('save_model', False)
        if save_model is True and user_callback_fn is not None:
            # this means this is the "best job" found
            # the user wants to save the model
            try:
                dir = os.path.join('aup_models', config.get('folder_name', None))
                previous_dir = os.getcwd()

                if os.path.exists('aup_models') is False:
                    os.makedirs('aup_models')

                if os.path.exists(dir) is True:
                    logger.warning('Deleting {}'.format(dir))
                    shutil.rmtree(dir)

                os.makedirs(dir)
                os.chdir(dir)

                user_callback_fn(*user_args, **user_kwargs)
            except Exception as e:
                raise e
            finally:
                os.chdir(previous_dir)

    return wrapper

def aup_flags(flags):
    """wrapper function for absl flags (or tf.app). 

    It will assign values to flags parameters using the given configuration file as the first argument when executed
    from the command line.
        
    Arguments:
        args {list} -- a list of unused arguments passed by app.run()
    """
    def decorator_wrapper(func):
        @functools.wraps(func)
        def wrapper(args):
            config = BasicConfig(**flags.__dict__).load(args[1])
            flags.__dict__.update()
            parameters = inspect.signature(func).parameters
            if parameters:
                logger.warning("TF FLAG main() should not accept arguments with Auptimizer, it has %s", 
                               parameters.keys())
                val = func({p:None for p in parameters})
            else:
                val = func()
            print_result(val)
        return wrapper
    return decorator_wrapper

def aup_save_model(callback_fn, *args, **kwargs):
    global user_callback_fn
    global user_args
    global user_kwargs

    user_callback_fn = callback_fn
    user_args = args
    user_kwargs = kwargs