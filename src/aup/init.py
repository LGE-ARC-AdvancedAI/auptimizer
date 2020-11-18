"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Initialize experiment
=====================

See :doc:`algorithm` for how to initialize the experiment search strategy.

Additional arguments
--------------------

.. program-output:: python3 -m aup.init -h

"""
import importlib
import json
import logging
import os
from collections import defaultdict

import click
import coloredlogs
from six.moves import input

from .Proposer import PROPOSERS
from .utils import LOG_LEVEL, get_default_connector, DEFAULT_AUPTIMIZER_PATH, get_from_options

logger = logging.getLogger("aup.init")


def _set_script(default=""):
    script = input("training script name [%s]:" % default) or default
    if not os.path.isfile(script):
        logger.critical("File %s doesn't exist, create it before experiment" % script)
        if not os.access(script, os.X_OK):
            logger.fatal("File is not self-executable, please do `chmod u+x %s`!" % script)
    return script


def _set_proposer(default=""):
    default = default or "random"
    config = dict()
    config["proposer"] = get_from_options("proposer", PROPOSERS.keys(), default=default)
    proposer = PROPOSERS[config['proposer']]
    mod = importlib.import_module("." + proposer, "aup.Proposer")
    cls = getattr(mod, proposer)
    config.update(cls.setup_config())
    return config


def _set_parallel(resource, cursor, default=1):
    cursor.execute("SELECT COUNT(*) FROM resource WHERE type=?;", (resource,))
    nparallel = cursor.fetchone()[0]
    val = [i for i in range(1, nparallel + 1)]
    nparallel = get_from_options("Number of parallel execution on %s, up to %d" %
                                 (resource, nparallel), val, default=default)

    return nparallel


def _get_workingdir(res, default=""):
    if res in ('node', 'aws'):
        cwd = input("working path on remote machine [%s]:" % default) or default
        if not cwd:
            logger.fatal("No path specified, exit!")
            exit(1)
    else:
        cwd = default or os.getcwd()
        cwd = input("working path, [default:%s]:" % cwd) or cwd
    return cwd


def _update(config, name, func, *args, **kwargs):
    if config[name] == "":
        config[name] = func(*args, **kwargs)
    else:
        config[name] = func(*args, default=config[name], **kwargs)
    return config


@click.command(name="Initialize experiment",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.option("--exp", "-e", default="experiment.json", help="Experiment configuration file (experiment.json)")
@click.option("--aup", "-c", default=DEFAULT_AUPTIMIZER_PATH, help="Auptimizer Folder path")
@click.option("--log", "-l", default="info", type=click.Choice(LOG_LEVEL.keys()), help="Log level")
@click.option("--overwrite/--no-overwrite", "-o/-no", default=False, help="overwrite existing file")
@click.option("--reload/--no-reload", default=False, help="reload existing experiment configuration")
def main(exp, aup, log, overwrite, reload):
    """Initialize experiment configuration for HPO
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Raises:
        Exception: If Auptimizer environment is not found.
    """
    coloredlogs.install(level=LOG_LEVEL[log], fmt="%(name)s - %(levelname)s - %(message)s")

    if os.path.isfile(exp) and not overwrite and not reload:
        logger.fatal("%s exists! Overwrite (-o) or change experiment name (-e)!", exp)
        exit(1)

    try:
        conn = get_default_connector(auppath=aup)
    except Exception as e:
        logger.fatal("Failed to get environment file, check aup.setup process")
        raise e

    config = defaultdict(str)
    if reload:
        with open(exp, 'r') as f:
            config.update(json.load(f))
    try:
        print("Hit ENTER to use the default value in brackets.")
        exp = input("Experiment configuration to be created [%s]:" % exp) or exp
        config = _update(config, 'script', _set_script)
        res = conn.get_resource_type()
        config = _update(config, 'resource', get_from_options, "computing resource for experiment", res)
        config = _update(config, 'n_parallel', _set_parallel, config["resource"], conn.cursor)
        config = _update(config, 'target', get_from_options, "max/min the score", ('max', 'min'))
        config = _update(config, 'workingdir', _get_workingdir, config["resource"])

        config.update(_set_proposer(default=config['proposer']))
    except KeyboardInterrupt:
        logger.info("Terminated by user")
    except Exception as e:
        logger.fatal("Failed to initialize experiment configuration")
        raise e
    finally:
        logger.info("Write experiment config to %s", exp)
        with open(exp, 'w') as f:
            json.dump(config, f, indent=2)


if __name__ == "__main__":
    main()
