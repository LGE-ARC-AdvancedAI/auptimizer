#!/usr/bin/env python3
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Auptimizer HPO main entry
=========================

:mod:`aup.__main__` is the Auptimizer main entry point for HPO experiments.

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
from .utils import get_available_port
from .dashboard import dashboard

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
@click.option("--launch_dashboard", is_flag=True, help="Launch the dashboard together with the experiment.")
@click.option("--dashboard_port", default=None, type=click.INT, help="Port for the dashboard frontend.")
def main(experiment_file, test, user, aup_folder, resume, log, sleep, launch_dashboard, dashboard_port):
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

    if not launch_dashboard and dashboard_port is not None:
        logger.fatal("dashbord_port value given without launch_dashboard flag given.")
        exit(0)

    if launch_dashboard:
        port = dashboard_port
        if port is None:
            port = get_available_port()
        logger.info('Dashboard started on 0.0.0.0:{}'.format(port))

    e = None
    if aup_folder:
        #TODO-the "connector" param in Experiment class is never customized
        e = Experiment(BasicConfig().load(experiment_file), auppath=aup_folder, **config)
    else:
        e = Experiment(BasicConfig().load(experiment_file), **config)
    if test:
        logger.info("# Testing")
        exit(0)

    if launch_dashboard:

        from .utils import load_default_env

        if aup_folder:
            db_path = load_default_env(aup_folder, log=None)["SQLITE_FILE"]
        else:
            from os.path import join
            db_path = load_default_env(join(".aup"), log=None)["SQLITE_FILE"]

        from multiprocessing import Process
        frontend = True
        proc = Process(target=dashboard._start_dashboard, args=(db_path, port, frontend))
        proc.start()

    logger.info("# Running Experiment")
    try:
        import signal
        original_sigint_handler = signal.getsignal(signal.SIGINT)
        e.add_suspend_signal()
        if resume == "none":
            e.start()
        else:
            e.resume(resume)
    except Exception as exp:
        if _log_level[log] > logging.DEBUG:
            logging.critical("use --log debug to track error details")
        else:
            raise exp
    finally:
        e.finish()
    if launch_dashboard:
        signal.signal(signal.SIGINT, original_sigint_handler)

        logger.info("Dashboard is still running on 0.0.0.0:{}".format(port))
        logger.info("To exit press CTRL+C...")
        proc.join()

if __name__ == "__main__":
    main()
