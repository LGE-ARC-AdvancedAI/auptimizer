"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Setup scripts for Auptimizer
============================

:mod:`aup.setup` is the entry point to set up the `.aup` environment.

See :doc:`environment` for more details.

Run it as:

  python -m aup.setup [env_template] ...

The templates are at ``Examples/2dfunc_diff_res/*.ini``.

Additional arguments
--------------------

.. program-output:: python3 -m aup.setup -h

APIs
----
"""
import json
import logging
import os
from shutil import rmtree
import sys

import click
import coloredlogs
from six.moves import input
from six.moves.configparser import ConfigParser

from .utils import get_default_username, LOG_LEVEL

# Name of resources in .aup database
GPU_RESOURCE_NAME = "gpu_mapping"
NODE_RESOURCE_NAME = "node_mapping"
AWS_RESOURCE_NAME = "aws_mapping"
logger = logging.getLogger("aup.setup")

PYTHON_EXEC = sys.executable

def _create_folder(folder, overwrite=False):
    """Create a folder"""
    if folder[0] == "~":
        folder = os.path.expanduser(folder)
    if os.path.exists(folder):
        if not overwrite:
            logger.fatal("Folder %s exists, please remove folder or use --overwrite", folder)
            raise Exception("Folder {} exists, please remove folder or use --overwrite".format(folder))
        else:
            rmtree(folder)
    try:
        os.mkdir(folder)
    except Exception as e:   # pragma: no cover
        logger.fatal("Failed to create folder, check the error message below")
        raise e
    return folder


def _set_resource(resource, config, target, start_rid):
    """Update resource allocation in Auptimizer and track resource ID"""
    if resource == "none":
        if config.has_option("Auptimizer", target):
            logger.warning("Remove conflict resource %s in Auptimizer.", target)
            config.remove_option("Auptimizer", target)
    else:
        if os.path.isfile(resource):
            with open(resource, 'r') as f:
                d = f.readlines()
        else:
            d = resource.split(",")
        if len(d) == 0 or d[0] == "":
            logger.critical("No resources for %s", target)
        resources = {}
        for i in d:
            resources[start_rid] = i.strip()
            start_rid += 1
        logger.info("Assign resource %s as %s", target, json.dumps(resources))
        config.set("Auptimizer", target, json.dumps(resources))
    return start_rid


def interactive_env(config):  # pragma: no cover
    config.add_section("Auptimizer")
    aup_path = input("Auptimizer Environment path - Auptimizer_PATH (Default is `.aup`):") or ".aup"
    config.set("Auptimizer", "Auptimizer_PATH", aup_path)
    aup_tmp = input("Auptimizer Temp folder - TMP_FOLDER (/tmp/auptmp):") or "/tmp/auptmp"
    config.set("Auptimizer", "TMP_FOLDER", aup_tmp)
    config.set("Auptimizer", "SQL_ENGINE", "sqlite")
    return config


def interactive_setup(env, config, cpu, gpu, node, aws, user, overwrite):  # pragma: no cover
    """
    Interactive user interface to get parameters for setup
    """
    print("Hit ENTER to use default values in brackets.")
    if env == ".":
        env = input("Load existing Auptimizer environment (env.ini file path), hit ENTER to initialize a new one:")

    if env.strip() == "":
        config = interactive_env(config)
    else:
        if not os.path.isfile(env):
            logger.fatal("Environment file %s does not exist, exit!", env)
            exit(1)
        try:
            config.read(env)
        except Exception as e:
            logger.fatal("Failed to load environment template %s using ConfigParser", env)
            raise e

    cpu = int(input("Number of CPUs for parallel jobs (%d):" % cpu) or cpu)
    gpu = input("GPU template file or comma-separated IDs (%s):" % gpu) or gpu
    node = input("Node template file (%s) or comma-separated nodes (user@ip:[port] [keyfile]):" % node) or node
    aws = input("AWS template file (%s) or comma-separated nodes (user@ip):[port] [keyfile]):" % aws) or aws
    user = input("Username (%s):" % user) or user

    if not overwrite:
        overwrite = input("Overwrite (y/N)").lower() == "y"

    return config, cpu, gpu, node, aws, user, overwrite


def setup(config, cpu, gpu, node, aws, user, overwrite, log):
    """
    Set up .aup environment

    :param config: env config
    :param cpu: number of cpu jobs
    :param gpu: gpu configuration file, 'none' if not exist
    :param node: node file, 'none' if not exist
    :param aws: aws file
    :param user: username, user specified > OS USER variable > 'default'
    :param overwrite: overwrite existing .aup environment
    :param log: log level for setupdb
    """
    folder_path = _create_folder(config.get("Auptimizer", "Auptimizer_PATH"), overwrite=overwrite)
    config.set("Auptimizer", "Auptimizer_PATH", folder_path)
    folder_path = _create_folder(config.get("Auptimizer", "TMP_FOLDER"), overwrite=True)
    config.set("Auptimizer", "TMP_FOLDER", folder_path)

    pending_commands = []

    rid = 1
    rid = _set_resource(gpu, config, GPU_RESOURCE_NAME, rid)
    rid = _set_resource(node, config, NODE_RESOURCE_NAME, rid)
    rid = _set_resource(aws, config, AWS_RESOURCE_NAME, rid)
    logger.debug("Create %d resources", rid)

    if config.get("Auptimizer", "SQL_ENGINE") == "sqlite":
        tmp_path = os.path.join(config.get("Auptimizer", "Auptimizer_PATH"), "sqlite3.db")
        config.set("Auptimizer", "SQLITE_FILE", tmp_path)
        pending_commands.append(PYTHON_EXEC + " -m aup.setupdb.sqlite %s --user %s --cpu %d --log %s" % (
            os.path.join(config.get("Auptimizer", "Auptimizer_PATH"), "env.ini"), user, cpu, log))
    else:
        logger.fatal("SQL engine %s is not implemented",
                     config.get("Auptimizer", "SQL_ENGINE"))
        exit(1)

    env_path = os.path.join(config.get("Auptimizer", "Auptimizer_PATH"), "env.ini")
    with open(env_path, "w") as f:
        logger.info("Write env.ini to %s", env_path)
        config.write(f)
    logger.info("Following commands are being executed:")
    for i, command in enumerate(pending_commands):
        logger.info("Executing command: " + command)
        rflag = os.system(command)
        if rflag != 0:
            logger.fatal("Failed in setup commands\nFollowing commands need finish manually (and debug):\n %s",
                         "\n".join(pending_commands[i:]))
            exit(1)


@click.command(name="Continuous Training Engine Setup",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("env", default=".", type=click.Path(exists=True))
@click.option("--cpu", default=4, help="Number of cores")
@click.option("--gpu", default='none', help="GPU file path")
@click.option("--node", default='none', help="Node file path")
@click.option("--aws", default='none', help="AWS file path")
@click.option("--user", default=None, help="User account for Auptimizer")
@click.option('--overwrite', is_flag=True, help="overwrite existing folder (and records!)")
@click.option("--log", default="info", type=click.Choice(LOG_LEVEL.keys()), help="Log level")
def main(env, cpu, gpu, node, aws, user, overwrite, log):  # pragma: no cover
    """ Create environment based on env file for Auptimizer
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        env {str}: Auptimizer config folder path. Default to create at `./.aup/`.  Leave empty to create a new one.
                   Or use the path of the filename (env.ini) to load predefined values (also use --overwrite).

    \b
    Raises:
        Exception: If failed to load the existing Auptimizer configuration file.
    """
    coloredlogs.install(level=LOG_LEVEL[log],
                        fmt="%(levelname)s - %(message)s")

    user = get_default_username(user)
    config = ConfigParser()
    config.optionxform = str

    if env == ".":  # interactive
        config, cpu, gpu, node, aws, user, overwrite = \
            interactive_setup(env, config, cpu, gpu, node, aws, user, overwrite)
    else:
        try:
            if not os.path.isfile(env):
                logger.info("Load default env.ini file.")
                env = os.path.join(env, "env.ini")
            config.read(env)
        except Exception as e:
            logger.fatal("failed to read %s", env)
            raise e
    setup(config, cpu, gpu, node, aws, user, overwrite, log)


if __name__ == "__main__":
    main()
