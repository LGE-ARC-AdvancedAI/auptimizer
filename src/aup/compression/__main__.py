#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

:mod:`aup.compression.__main__` is the Auptimizer main entry point for compression experiments.

Use it as::

  python -m aup.compression <experiment configuration> 

The usage is detailed in :doc:`compression`.

Additional arguments
--------------------

.. program-output:: python3 -m aup.compression -h

"""

import os
import json
import logging
import re
import signal
import sys
import time
import signal

import click
import coloredlogs

from ..EE.Resource import get_resource_manager
from ..EE.Experiment import Experiment
from ..EE.Job import Job
from .. import BasicConfig
from ..utils import get_default_username, get_default_connector, check_missing_key, set_default_keyvalue, get_available_port, load_default_env
from .utils import adjust_compression_config, run_non_automatic_experiment, verify_compression_config
from ..dashboard import dashboard


_log_level = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "error": logging.ERROR}
logger = logging.getLogger("aup.compression")


@click.command(name="Model Compression", context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("experiment_file", type=click.Path(exists=True))
@click.option("--automatic", is_flag=True, help="Whether or not running an automatic compression experiment with hyperparameter optimization.")
@click.option("--user", default=None, help="User name for job scheduling")
@click.option("--aup_folder", default=os.path.join(".aup"), help="Specify customized aup folder")
@click.option("--resume", default="none", help="Resume from previous task")
@click.option("--log", default="info", type=click.Choice(["debug", "info", "warn", "error"]), help="Log level")
@click.option("--sleep", default=1, type=click.FLOAT, help="Sleep interval to sync updates")
@click.option("--launch_dashboard", is_flag=True, help="Launch the dashboard together with the experiment.")
@click.option("--dashboard_port", default=None, type=click.INT, help="Port for the dashboard frontend.")
def main(experiment_file, automatic, user, aup_folder, resume, log, sleep, launch_dashboard, dashboard_port):
    """Compress a given model.

    \b
    Arguments:
        experiment_file {str} -- Compression configuration
    """
    coloredlogs.install(level=_log_level[log],
                        fmt="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")    
    
    user = get_default_username(user)
    exp_config = BasicConfig().load(experiment_file)
    exp_config = verify_compression_config(exp_config)
    exp_config["compression"] = adjust_compression_config(exp_config["compression"])

    set_default_keyvalue("cwd", os.getcwd(), exp_config, log=logger)
    set_default_keyvalue("workingdir", exp_config.get("cwd", os.getcwd()), exp_config, log=logger)

    if not launch_dashboard and dashboard_port is not None:
        logger.fatal("dashbord_port value given without launch_dashboard flag given.")
        exit(0)

    if launch_dashboard:
        port = dashboard_port
        if port is None:
            port = get_available_port()
        logger.info('Dashboard started on 0.0.0.0:{}'.format(port))

        if aup_folder:
            db_path = load_default_env(aup_folder, log=None)["SQLITE_FILE"]
        else:
            from os.path import join
            db_path = load_default_env(join(".aup"), log=None)["SQLITE_FILE"]

        from multiprocessing import Process
        frontend = True
        proc = Process(target=dashboard._start_dashboard, args=(db_path, port, frontend))
        proc.daemon = True
        proc.start()

        original_sigint_handler = signal.getsignal(signal.SIGINT)

    if automatic:
        config = {
            "username": get_default_username(user),
            "sleep_time": sleep,
        }
        if aup_folder:
            e = Experiment(exp_config, auppath=aup_folder, **config)
        else:
            e = Experiment(exp_config, **config)

        logger.info("# Running automatic compression experiment")
        try:  
            e.add_suspend_signal()
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
    else:
        _, finish = run_non_automatic_experiment(exp_config, aup_folder, user)
        finish()

    if launch_dashboard:
        signal.signal(signal.SIGINT, original_sigint_handler)

        logger.info("Dashboard is still running on 0.0.0.0:{}'".format(port))
        logger.info("To exit press CTRL+C...")
        proc.join()

if __name__ == "__main__":
    main()
