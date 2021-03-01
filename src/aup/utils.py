#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Utility functions
=================

Supporting functions used by other modules.

APIs
----
"""
from __future__ import print_function

import sys

import logging
import os
from os import path
from six.moves import input
from six.moves.configparser import ConfigParser
import paramiko as pm
from paramiko import SFTPClient

from .aup import BasicConfig, print_result

logger = logging.getLogger(__name__)

LOG_LEVEL = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "error": logging.ERROR}

DEFAULT_AUPTIMIZER_PATH = path.join(".aup")  # use local as default


def check_missing_key(config, key, msg, log=logger):
    """Verify important key is present, otherwise raise exception

    :param config: configuration
    :type config: dict
    :param key: key name
    :type key: str
    :param msg: warning message when key is not present
    :type msg: str
    :param log: logger obj to trace where the function is called, default is aup.utils
    :type log: logging.Logger
    """
    if key not in config:
        log.error(msg)
        raise KeyError(msg)


def get_default_connector(auppath=DEFAULT_AUPTIMIZER_PATH, log=logger):
    """Get default connector based on .env

    :param auppath: aup environment folder, contains `env.ini` file
    :param log: logger obj to trace where the function is called, default is aup.utils
    :type log: logging.Logger
    :return: Database connector
    :rtype: :mod:`aup.ET.Connector.AbstractConnector`
    """
    config = load_default_env(auppath=auppath)
    log.debug(config)
    if "SQL_ENGINE" not in config:
        raise KeyError("No SQL setup for SQL_ENGINE in %s"%auppath)
    elif config["SQL_ENGINE"] == "sqlite":
        from .ET.Connector.SQLiteConnector import SQLiteConnector
        if "SQLITE_FILE" not in config:
            raise KeyError("SQLITE_FILE is missing in %s for sqlite setup"%auppath)
        logger.info("Use default connector at %s" % config["SQLITE_FILE"])
        return SQLiteConnector(path.expanduser(config["SQLITE_FILE"]))
    else:
        raise KeyError("SQL setup for %s is not supported" % config["SQLITE_FILE"])


def get_default_username(username=None):
    """
    Get default username for Auptimizer
    
    :param username: username
    :return: username
    """
    if username is None:
        if "USER" not in os.environ or not os.environ["USER"]:
            logger.critical("No USER specified, use `default`.")
            return "default"
        else:
            logging.info("Using default user %s" % os.environ["USER"])
            return os.environ["USER"]
    else:
        logging.debug("For user %s" % username)
        return username


def get_from_options(msg, values, default=None):  # pragma: no cover
    """
    helper function to ask from user input, and validate it is one of the permitted values.
    
    :param msg: message to ask the user
    :param values: permitted values
    :param default: default value when user skip, if None, values[0] is used.
    :return: value with the same type as values[0]
    """
    if default is None:
        default = values[0]
    v = input(msg + " [%s]:" % str(default)) or default
    v = type(default)(v)
    if v not in values:
        logger.fatal("%s is not valid value, choose from [%s]" % (v, "|".join([str(v) for v in values])))
        exit(1)
    return v


def load_default_env(auppath=DEFAULT_AUPTIMIZER_PATH, log=logger, use_default=True):
    """Load default environment variables for aup.
    Search recursively to upper folder

    :param auppath: aup environment folder, contains `env.ini` file
    :type auppath: str
    :param log: logger obj to trace where the function is called, default is aup.utils, 
                if None, then no logging is performed
    :type log: logging.Logger
    :param use_default: if auppath is empty, use user's home folder instead.
    :type use_default: bool
    :return: key-value of parameters
    :rtype: dict
    """
    if not path.isfile(path.join(auppath, "env.ini")):
        if use_default:
            auppath = path.join(path.expanduser("~"), ".aup")
            if log is not None:
                log.warning("Use default env at %s" % auppath)
            if not path.isfile(path.join(auppath, "env.ini")):  # pragma: no cover
                raise Exception("Failed to find env.ini")
        else:
            raise ValueError("Auptimizer folder %s is missing" % auppath)
    if log is not None:
        log.info("Auptimizer environment at %s", auppath)
    config = ConfigParser()
    config.optionxform = str
    config.read(path.join(auppath, "env.ini"))
    return {i[0]: i[1] for i in config.items("Auptimizer")}


def parse_result(result, log=logger):
    """
    Parse the result printed by :func:`print_result`

    :param log: logger obj to trace where the function is called, default is aup.utils
    :type log: logging.Logger
    :param result: result string
    :type result: str
    :return: result for Auptimizer update
    :rtype: float
    """
    result = result.splitlines()
    for r in result:
        if "#Auptimizer:" in r:
            result = r[12:]
            try:
                return float(result)
            except ValueError:
                logger.debug("Cannot convert the result to float - trying to convert the result to a list")
                return [float(f) for f in result.split(',')]

    log.fatal("Result `%s` is not created by aup", result)
    raise ValueError("Result `%s` is not created by aup print_result" % result)

def parse_one_line(result, log=logger):
    if "#Auptimizer:" in result:
        result = result[12:]
        try:
            return [float(result)]
        except ValueError:
            logger.debug("Cannot convert the result to float - trying to convert the result to a list")
            return [float(f) for f in result.split(',')]

    return None


def set_default_keyvalue(key, value, d, inplace=True, log=logger):
    """Set default value for dict if key is not defined

    :param key: key name
    :type key: str
    :param value: key value
    :type value: object
    :param d: target dict object to be updated
    :type d: dict
    :param inplace: whether update in place.
    :type inplace: boolean
    :param log: logger obj to trace where the function is called, default is aup.utils
    :type log: logging.Logger
    :return: updated dict
    :rtype: dict
    """
    if not inplace:
        d = d.copy()
    if key not in d:
        log.warning("Using default value %s for %s" % (value, key))
        d[key] = value
    return d

def block_until_ready(client, socket, env):
    """Block current thread until we receive the ready status
    :param client: the current connected client
    :type client: SSHClient
    :param socket: socket connection to machine where job is executed
    :param env: environment to set up on the remote machine
    """
    from time import sleep
    import paramiko as pm

    sleep_time_s = 0.1
    timeout_time_s = 5
    nop_linux_command = ":"

    while socket.channel.exit_status_ready() == False:
        client.exec_command(nop_linux_command, timeout=timeout_time_s, environment=env)
        logger.debug("Command executed successfully, now sleeping")
        sleep(sleep_time_s)

def open_sftp_with_timeout(client, timeout=5):
    """
    SFTP Connection to transfer files and environment between Auptimizer source machine and remote machine.
    """
    t = client.get_transport()
    chan = t.open_session(
            window_size=None, max_packet_size=None, timeout=timeout
        )
    if chan is None:
        return None
    chan.invoke_subsystem("sftp")
    return SFTPClient(chan)

def get_available_port():
    """
    Returns first open port available.
    """
    from socket import socket
    with socket() as s:
        s.bind(('',0))
        port = int(s.getsockname()[1])
    return port