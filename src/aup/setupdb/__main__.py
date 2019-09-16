#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Set up database for Auptimizer
==============================

Set up the database for **Auptimizer** based on the specified environment ini file.

It is called automatically when user sets up the **Auptimizer** for the first time.

Use it to reset database to the **original** state.

Additional arguments
--------------------

.. program-output:: python3 -m aup.setupdb -h

"""

import logging
import os

import click
import coloredlogs
from six.moves.configparser import ConfigParser

from ..utils import LOG_LEVEL

logger = logging.getLogger("aup.setupdb")


@click.command(name="Setup database",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--user", default=os.environ["USER"], help="username for history tracking")
@click.option("--cpu", default=4, type=click.INT, help="number of CPUs to run parallel")
@click.option("--name", default="localhost", help="resource name, not used")
@click.option("--log", default="info", type=click.Choice(["debug", "info", "warn", "error"]), help="Log level")
def main(env_file, user, cpu, name, log):
    """Create Database for *Auptimizer* env.ini.

    \b
    Arguments:
        env_file {str}: Auptimizer environment file
    """
    config = ConfigParser()
    config.read(env_file)

    coloredlogs.install(level=LOG_LEVEL[log], fmt="%(name)s - %(levelname)s - %(message)s")

    if config.get("Auptimizer", "SQL_ENGINE") == "sqlite":
        from . import sqlite
        sqlite.create_database(config, [user], cpu, name)
    else:
        raise KeyError("%s is not implemented" % config.get("Auptimizer", "SQL_ENGINE"))


if __name__ == "__main__":
    main()
