#!/usr/bin/env python3
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Auptimizer main entry
=====================

:mod:`aup.__main__` is the Auptimizer main entry point.

Use it as::

  python -m aup <experiment configuration>

The usage is detailed in :doc:`experiment`.

Additional arguments
--------------------

.. program-output:: python3 -m aup -h

"""

import logging

import click
import coloredlogs

from . import Experiment, BasicConfig
from .utils import get_default_username

_log_level = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "error": logging.ERROR}
logger = logging.getLogger("aup")


@click.command(name="Auptimizer training", context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("experiment_file", type=click.Path(exists=True))
@click.option("--test", is_flag=True, help="Test one case to verify the code is working")
@click.option("--user", default=None, help="User name for job scheduling")
@click.option("--aup_folder", default=None, help="Specify customized aup folder")
@click.option("--resume", default="none", help="Resume from previous task")
@click.option("--log", default="info", type=click.Choice(["debug", "info", "warn", "error"]), help="Log level")
@click.option("--sleep", default=1, type=click.FLOAT, help="Sleep interval to sync updates")
def main(experiment_file, test, user, aup_folder, resume, log, sleep):
    """Auptimizer main function for HPO experiment
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        experiment_file {str} -- Experiment configuration (can be created by `python -m aup.init`).
    """
    coloredlogs.install(level=_log_level[log],
                        fmt="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")
    config = {
        "username": get_default_username(user),
        "sleep_time": sleep,
    }

    if aup_folder:
        #TODO-the "connector" param in Experiment class is never customized
        e = Experiment(BasicConfig().load(experiment_file), auppath=aup_folder, **config)
    else:
        e = Experiment(BasicConfig().load(experiment_file), **config)
    if test:
        logger.info("# Testing")
        exit(0)

    logger.info("# Running Experiment")
    try:
        if resume == "none":
            e.start()
        else:
            e.resume(resume)
        e.finish()
    except Exception as e:
        if _log_level[log] > logging.DEBUG:
            logging.critical("use --log debug to track error details")
        else:
            raise e

if __name__ == "__main__":
    main()
