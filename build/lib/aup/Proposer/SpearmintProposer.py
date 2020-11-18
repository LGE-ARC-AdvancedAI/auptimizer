"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.Proposer.SpearmintProposer
==============================

Re-implementation of Spearmint.  Most of the Spearmint code has not been changed
Mainly wrap main.py

Be aware - all variables are vectorized except size=1 case.  (different from spearmint original implementation)

The original source is forked from `Spearmint github commit 70309f0
<https://github.com/JasperSnoek/spearmint/tree/master/spearmint>`_.

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

============= ============== ========================================
Name          Default value  Explanation
============= ============== ========================================
proposer      -              spearmint
engine        GPEIOptChooser
engine_config -              Options for spearmint chooser
grid_size     20000          Option for spearmint
n_samples     -              Total number of trials to sample
random_seed   0              [Optional] seed for random generator
spearmint_dir spearmint      Spearmint working directory
============= ============== ========================================

Specific parameters for ``parameter_config``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

======= ==========================================================================
Name    Explanation
======= ==========================================================================
name    name of the variable, will be used in the job config, i.e. training code
type    type of the parameter to be sampled: choose from "float","int","choice"
range   range of the parameter.  For "choice", list all the feasible values
======= ==========================================================================

APIs
----
"""
import importlib
import logging
import os
import shutil

from six.moves import input

from .AbstractProposer import AbstractProposer
from .spearmint import ExperimentGrid
from ..aup import BasicConfig
from ..utils import set_default_keyvalue, check_missing_key, get_from_options

logger = logging.getLogger(__name__)


class SpearmintProposer(AbstractProposer):
    def __init__(self, config):
        super(SpearmintProposer, self).__init__(config)

        if os.path.isdir(config["workingdir"]):  # local folder exist
            set_default_keyvalue("spearmint_dir",
                                 os.path.join(config["workingdir"], "spearmint"),
                                 config, log=logger)
        else:  # local folder not exist (esp. run remotely)
            set_default_keyvalue("spearmint_dir", "spearmint", config, log=logger)
        self.expt_dir = config["spearmint_dir"]
        set_default_keyvalue("random_seed", 0, config, log=logger)
        set_default_keyvalue("engine", "GPEIChooser", config, log=logger)
        set_default_keyvalue("engine_config", {}, config, log=logger)
        set_default_keyvalue("grid_size", 20000, config, log=logger)

        self.nSamples = config["n_samples"]
        self.seed = config["random_seed"]
        self.target = -1 if config["target"] == "max" else 1
        self.variables = []
        self.grid_size = config["grid_size"]

        for param in config["parameter_config"]:
            p = self.parse_param_config(param)
            if "job_id" == p['name']:
                msg = "`job_id` is preserved for HPO"
                logger.fatal(msg)
                raise ValueError(msg)
            if p["type"] == "choice":
                p["type"] = "enum"
            set_default_keyvalue('size', 1, p)
            self.variables.append(BasicConfig(**p))

        try:
            module = importlib.import_module(".spearmint.chooser." + config["engine"], package='aup.Proposer')
            self.chooser = module.init(self.expt_dir, config["engine_config"])
            self.verify_config(config)
        except ImportError:
            msg = "%s doesn't exist in spearmint" % config["engine"]
            logger.fatal(msg)
            raise KeyError(msg)

    @staticmethod
    def setup_config():  # pragma: no cover
        config = dict()
        logger.critical("The following step only setup the basic configuration, edit file direct for advanced tuning.")
        config['engine'] = get_from_options("HPO Engine, `engine`,", ["GPEIOptChooser"])
        config['engine_config'] = dict()
        config['grid_size'] = int(input("Grid size for hyperparameters, `grid_size`, [20000]:") or 20000)
        config['n_samples'] = int(input("number of model samples to draw randomly, `n_samples`, [1]:") or 1)
        config['random_seed'] = int(input("random seed, `random_seed`, [0]:") or 0)
        config.update(AbstractProposer.setup_config())
        for i in config['parameter_config']:
            i.update({'size': 1})
        return config

    def get_param(self, **kwargs):
        expt_grid = ExperimentGrid(self.expt_dir, self.variables, self.grid_size, self.seed)
        grid, values, durations = expt_grid.get_grid()
        candidates = expt_grid.get_candidates()
        pending = expt_grid.get_pending()
        complete = expt_grid.get_complete()

        job_id = self.chooser.next(grid, values, durations, candidates, pending, complete)

        if isinstance(job_id, tuple):
            (job_id, candidate) = job_id
            job_id = expt_grid.add_to_grid(candidate)

        expt_grid.set_submitted(job_id, 0)
        job_config = expt_grid.get_params(job_id)
        for i in job_config:
            if len(job_config[i]) == 1:  # spearmint returns list, other methods return value.
                job_config[i] = job_config[i][0]
            else:
                raise NotImplementedError("Parameter with dimension larger than 1 is not supported yet")
        job_config["job_id"] = job_id
        expt_grid.set_running(job_id)
        self.current_proposal = job_config
        return self.current_proposal

    def save(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    def reload(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    def update(self, score, job):
        ExperimentGrid.job_complete(self.expt_dir, job.config["job_id"], score * self.target, 0)

    def failed(self, job):
        super(SpearmintProposer, self).failed(job)
        ExperimentGrid.job_broken(self.expt_dir, job.config["job_id"])

    def verify_config(self, config):
        check_missing_key(config, "n_samples", "Specify number of samples to randomly draw", log=logger)

        if os.path.exists(self.expt_dir):
            logger.warning("Removing folder %s" % self.expt_dir)
            shutil.rmtree(self.expt_dir)
        os.mkdir(self.expt_dir)
        return config
