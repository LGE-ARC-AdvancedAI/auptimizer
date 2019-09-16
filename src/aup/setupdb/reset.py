#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Reset database
==============

Reset database **without** removing experiment history.

Additional arguments
--------------------

.. program-output:: python3 -m aup.setupdb.reset -h

"""
import click
from six.moves.configparser import ConfigParser


@click.command(name="Reset DB resource table",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("env_file", type=click.Path(exists=True))
def main(env_file):
    """Reset database defined in env.ini file, history remains.
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        env_file {str}: Auptimizer environment file
    """
    config = ConfigParser()
    config.read(env_file)

    if config.get("Auptimizer", "SQL_ENGINE") == "sqlite":
        from . import sqlite
        sqlite.reset(config)
    else:
        raise KeyError("%s is not implemented" % config.get("Auptimizer", "SQL_ENGINE"))


if __name__ == "__main__":
    main()
