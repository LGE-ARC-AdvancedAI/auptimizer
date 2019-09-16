"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Convert python code for Auptimizer automatically
================================================

See :doc:`experiment` for how to convert a job to a **Auptimizer** Experiment.

Basic Usage
-----------

::

    python convert.py origin.py experiment.json demo_func

Additional arguments
--------------------

.. program-output:: python -m aup.convert -h

Example
-------

See `Examples/demo`:


APIs
----

"""
import json
import logging
import os
import stat

import click


def get_param(experiment_file):
    """Parse experiment file to retrieve hyperparameter names

    :param experiment_file: JSON file of the experiment
    :return: list of variable names
    :rtype: [String]
    """
    with open(experiment_file) as f:
        j = json.load(f)
    try:
        return [i["name"] for i in j["parameter_config"]]
    except KeyError as e:
        if "parameter_config" not in j:
            logging.fatal("parameter_config not in the experiment config")
        else:
            logging.fatal("name not in parameter_config")
        raise e


def get_output_name(experiment_file):
    """Retrieves the Python script to be executed from the experiment json file"""
    with open(experiment_file) as f:
        j = json.load(f)
    try:
        return j["script"]
    except KeyError as e:
        logging.fatal("script need to be defined in experiment json")
        raise e


def add_shenbang(script):
    """
    Makes the Python script executable.
    """
    if script.splitlines()[0][:2] != "#!":
        #
        if os.name == "posix":
            return "#!/usr/bin/env python\n" + script
        else:
            logging.critical('Be cautious, add #!"C:\\Python33\\python.exe", make sure it executable on Windows')
            return '#!"C:\\Python33\\python.exe\n' + script
    else:
        return script


def add_main(script):
    """
    Adds a main function to the executable Python file.
    """
    if "__main__" in script:
        logging.critical("__main__ is already defined in the script.  Make sure no duplicated __main__ blocks in output.")
    return script + """\nif __name__ == "__main__":
    import sys
    from aup import BasicConfig, print_result
    if len(sys.argv) != 2:
        print("config file required")
        exit(1)
    config = BasicConfig().load(sys.argv[1])
    aup_wrapper(config)\n"""


def add_func(script, func_name, variables):
    """
    Adds wrapper function to the python script.
    """
    arguments = ",".join(["{0}=config['{0}']".format(i) for i in variables])
    wrapper_script = """\ndef aup_wrapper(config):
    res = {0}({1}) 
    print_result(res)\n""".format(func_name, arguments)
    return script + wrapper_script
    # TODO-handle exception: func_name does not have any return value (need some ast parsing)
    # TODO-"config" is not used/referenced in "aup_wrapper" function


@click.command(name="auto convert script for Auptimizer",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("script", type=click.Path(exists=True))
@click.argument("exp_json", type=click.Path(exists=True))
@click.argument("func_name", type=click.STRING)
@click.option("-o", "--output", type=click.STRING, default=None,
              help="output file name")
def main(script, exp_json, func_name, output):
    """Convert script for Auptimizer
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        script {str} -- Script name to train an ML model and return result
        exp_json {str} -- JSON file name contrains experiment configuration (e.g. hyperparameter)
        func_name {str} -- Name of the main function in the script for the training

    \b\n
    Raises:
        Exception: If the script is not self-executable.
    """
    variable_names = get_param(exp_json)
    script = open(script).read()
    script = add_shenbang(script)
    script = add_func(script, func_name, variable_names)
    script = add_main(script)
    if output is None:
        output = get_output_name(exp_json)
    with open(output, 'w') as f:
        f.write(script)
    if os.name == "posix":
        os.chmod(output, stat.S_IRWXU)

    else:
        logging.critical("Non-*nix OS is not fully supported, change permission by yourself.")

    if not os.access(output, os.X_OK):
        raise Exception("Failed at the last step - script %s is not executable" % output)


if __name__ == "__main__":
    main()
