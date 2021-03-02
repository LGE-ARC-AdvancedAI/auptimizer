"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""
import json
import logging
import signal
import sys
import _thread
import threading
import time

from ..EE.Resource import get_resource_manager
from ..aup import BasicConfig
from ..EE.Job import Job
from ..utils import get_default_username, get_default_connector, check_missing_key


SERIALIZATION_SEPARATOR = "."
logger = logging.getLogger(__name__)
hyperparams_params = ["range", "type", "interval", "n"]


def verify_compression_config(config):
    """
    verify the experiment configuration is fulfilled for experiment

    :param config: experiment configuration
    :type config: dict
    :return: config if verified
    :rtype: dict
    """
    check_missing_key(config, "name", "Missing required value for 'script'.", log=logger)
    check_missing_key(config, "script", "Missing required value for 'script'.", log=logger)
    check_missing_key(config, "resource", "Missing required value for 'resource'", log=logger)
    check_missing_key(config, "compression", "Missing required map 'compression'", log=logger)
    if "compression_framework" not in config["compression"]:
        check_missing_key(config["compression"], "framework", "Missing required value for 'compression.framework'", log=logger)
    if "compression_type" not in config["compression"]:
        check_missing_key(config["compression"], "type", "Missing required value for 'compression.type'", log=logger)
    check_missing_key(config["compression"], "compressor", "Missing required value for 'compression.compressor'", log=logger)
    check_missing_key(config["compression"], "config_list", "Missing required value for 'compression.config_list'", log=logger)
    return config


def run_non_automatic_experiment(exp_config, aup_folder, user=None, eid=None, start=True):
    """
    Non-automatic experiment pipeline, separated into a different function for unit test purposes
    :param exp_config: experiment configuration
    :type exp_config: dict
    :param aup_folder: the folder containing the .aup files
    :type aup_folder: str
    :param user: the username
    :type user: str
    :param eid: eid of the experiment, if re-running
    :type eid: int
    :param start: whether or not to start the experiment immediately
    :type start: bool
    """
    user = get_default_username(user)
    create_only = False

    exp_config["parameter_config"] = []
    connector = get_default_connector(auppath=aup_folder, log=logger)
    if "resource_args" in exp_config:
        resource_manager = get_resource_manager(exp_config["resource"], connector,
                                                n_parallel=1, auppath=aup_folder,
                                                maximize=True,
                                                **exp_config["resource_args"],
                                                workingdir=exp_config['workingdir'],
                                                script=exp_config['script'], one_shot=True)
    else:
        resource_manager = get_resource_manager(exp_config["resource"], connector,
                                                n_parallel=1, auppath=aup_folder,
                                                maximize=True,
                                                workingdir=exp_config['workingdir'],
                                                script=exp_config['script'], one_shot=True)

    if eid is None:
        if start is True:
            eid = resource_manager.connector.start_experiment(user, exp_config["name"], json.dumps(exp_config))
        else:
            eid = resource_manager.connector.create_experiment(user, exp_config["name"], json.dumps(exp_config))
            create_only = True
    else:
        resource_manager.connector.start_experiment_by_eid(eid)
    resource_manager.eid = eid
    resource_manager.save_model = False

    if "runtime_args" in exp_config:
        runtime_args = exp_config['runtime_args']
    else:
        runtime_args = {}
    logger.info("Experiment %d is created" % eid)
    logger.debug("Experiment config is %s" % json.dumps(exp_config))

    if create_only:
        connector.close()
        return eid, None

    def _check_status():
        if connector is None or eid is None:
            logger.warning("Could not start thread for checking external experiment stopping requests.")
            return
        while True:
            try:
                if connector.is_closed():
                    logger.debug("Closing down clean-up thread.")
                    return
                status = connector.maybe_get_experiment_status(eid)
                if status == "REQUEST_STOP":
                    return _thread.interrupt_main()
            except Exception as ex:
                logger.critical("Error in clean-up thread: {}".format(ex))
            finally:
                time.sleep(5)
    request_stop_thr = threading.Thread(target=_check_status)
    request_stop_thr.start()

    rid = resource_manager.get_available(user, exp_config["resource"])
    if rid is None:
        logger.warning("Not enough resources to run compression")
        return eid

    finished = False
    def update(score, jid):
        nonlocal finished
        if score == "ERROR":
            logger.fatal("Compression job {} failed".format(job.jid))
            resource_manager.finish_job(job.jid, None, "FAILED")
        else:
            logger.critical("Compression job {} finished successfully with result {}".format(job.jid, score))
            resource_manager.finish_job(job.jid, score, "FINISHED")
        finished = True

    logger.info("# Running one-time compression experiment {}".format(eid))
    job_config = BasicConfig(**exp_config["compression"])
    job_config["save_model"] = True
    job_config["folder_name"] = "models_{}".format(eid)
    job = Job(exp_config["script"], job_config, exp_config["workingdir"], retries=0)
    
    def _suspend(sig, frame):
        logger.fatal("Compression ended at user's request")
        resource_manager.suspend()
        resource_manager.finish_job(job.jid, None)
        resource_manager.finish(status="STOPPED")
        connector.close()
        if request_stop_thr is not None:
            request_stop_thr.join()
        sys.exit(1)
    signal.signal(signal.SIGINT, lambda x, y: _suspend(x, y))

    def _force_refresh(sig, frame):
        # currently useful for async resource manager timers
        resource_manager.refresh()
    signal.signal(signal.SIGUSR1, lambda x, y: _force_refresh(x, y))
    
    job.jid = resource_manager.connector.job_started(eid, rid, job_config)
    resource_manager.run_job(job, rid, exp_config, update, **runtime_args)

    def _finish_callback():
        nonlocal finished
        while not finished:
            time.sleep(1)
        resource_manager.finish(status="FINISHED")
        connector.close()
        if request_stop_thr is not None:
            request_stop_thr.join()

    return eid, _finish_callback


def _extract_compression_hyperparameters(params):
    """
    Helper function used to extract a list of compression hyperparameters from 
    config_list mappings.
    This function searches recursively in compression config_list entries for keywords 
    mapped to dictionaries containing a "range" and "type", and resolves for them a 
    serialized name based on the depth at which they are found.

    :param params: config_list element
    :type params: dict
    :return: list of hyperparameters as dictionaries containing "name", "range" and 
    "type"
    :rtype: list
    """
    args = []
    for key, val in params.items():
        if isinstance(val, dict):
            if "type" in val:
                args += [{
                    "name": key,
                    **{key: val[key] for key in hyperparams_params if key in val},
                }]
            else:
                ret = _extract_compression_hyperparameters(val)
                ret = [{
                        **val,
                        "name": "{}{}{}".format(key, SERIALIZATION_SEPARATOR, val["name"]),
                    } for val in ret
                ]
                args += ret
    return args


def translate_compression_config(config):
    """
    Helper function used to parse the experiment config for automatic compression experiments
    into the HPO experiment config format. 

    :param config: experiment config
    :type config: dict
    :return: modified experiment config
    :rtype: dict
    """
    config = config.copy()

    # Expand op names (resolve "expand_op_names" keyword in entries)
    new_config_list = []
    for param in config["compression"]["config_list"]:
        if ("expand_op_names" not in param or param["expand_op_names"]) and \
           "op_names" in param:
            for op_name in param["op_names"]:
                # For each op_name in "op_names", create a separate config_list entry
                # with only that op_name and otherwise all other key-value pairs (e.g. 
                # "op_types", "sparsity", "quantize_type" etc.)
                new_config_list += [{
                        **{"op_names": [op_name]}, 
                        **{key: val for key, val in param.items() 
                            if key not in ("expand_op_names", "op_names")}
                    }]
        else:
            if ("expand_op_names" not in param or param["expand_op_names"]) and \
               "op_names" not in param:
                logger.debug("No op_names param supplied in config_list for expand_op_names, " +
                             "can not supply individual parameters to each layer.")
            new_config_list += [{
                key: val for key, val in param.items()
                if key not in ("expand_op_names",)
            }]
    config["compression"]["config_list"] = new_config_list

    # Resolving compression hyperparams to previous parameter_config format
    # The following code block adds a serialization name to all hyperparameters found in config_list
    compression_params = [] # auxiliary list of serialized compression hyperparams names (strings)
    config["parameter_config"] = []
    for idx, param in enumerate(config["compression"]["config_list"]):
        config["parameter_config"] += [{
                **param,
                "name": "{}{}{}".format(idx, SERIALIZATION_SEPARATOR, param["name"]),
            } for param in _extract_compression_hyperparameters(param)
        ]
    compression_params += [param["name"] for param in config["parameter_config"]]
    
    config = BasicConfig(**config)
    return config, compression_params


def deserialize_compression_proposal(config, compression_params, proposal):
    """
    Helper function used to deserialize a proposal meant for compression from its usual
    HPO format into a NNI-compatible config_list format.
    The output of this function is normally passed to the user script, where it is loaded
    using BasicConfig.

    :param config: full experiment config
    :type config: dict
    :param compression_params: list of names of compression params to filter proposal by
    :type compression_params: list
    :param proposal: proposal generated by an auptimizer proposer
    :type proposal: dict
    :return: deserialized job configuration
    :rtype: dict
    """
    new_proposal = config["compression"].copy()
    for param in compression_params:
        full_param = param.split(SERIALIZATION_SEPARATOR)
        index = int(full_param[0]) # the first string until . is always the config_list index
        original_key = full_param[-1] # the last string is always the original key of the config_list entry
        cdict = new_proposal["config_list"][index]
        # Parse the config_list entry recursively until arriving at max depth
        for part in full_param[1:-1]:
            cdict = cdict[part]
        cdict[original_key] = proposal[param] # assign the actual proposed value for the param, instead of the hyperparameter "range" and "type" format
    new_proposal.update({key: val for key, val in proposal.items() if key not in compression_params})
    return new_proposal


def adjust_compression_config(config):
    """
    Adjust certain config parameters
    :param config: experiment configuration
    :type config: dict
    :return: config adjusted
    :rtype: dict
    """
    # In order to avoid possible conflicts ("framework", "type" etc. are too ubiquitous parameter names)
    for old_name, new_name in [
        ("type", "compression_type"), 
        ("framework", "compression_framework")
    ]:
        if old_name in config:
            config[new_name] = config[old_name]
            del config[old_name]
    return config
