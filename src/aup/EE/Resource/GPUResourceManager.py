"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.GPUResourceManager
==================================

Resource manager for Single GPU machine.

It supports:

1. Multiple Cards
2. Multiple jobs running on a shared card (no control over GPU resource limit)

APIs
----
"""
import json
import logging
import os

from .CPUResourceManager import CPUResourceManager
from ...utils import check_missing_key, load_default_env, DEFAULT_AUPTIMIZER_PATH

logger = logging.getLogger(__name__)


def _load_gpu_mapping(auppath=DEFAULT_AUPTIMIZER_PATH):
    """
    loads GPU mapping based on environment and config
    """
    config = load_default_env(auppath=auppath)
    check_missing_key(config, "gpu_mapping", "Missing gpu_mapping parameter in aup config file", log=logger)
    # need to reverse the type for GPU mapping
    d = json.loads(config["gpu_mapping"])
    return {int(k): str(d[k]) for k in d}


class GPUResourceManager(CPUResourceManager):
    def __init__(self, connector, n_parallel, auppath=DEFAULT_AUPTIMIZER_PATH, *args, **kwargs):
        super(GPUResourceManager, self).__init__(connector, n_parallel, *args, **kwargs)
        self.mapping = _load_gpu_mapping(auppath=auppath)

    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        logger.debug("Job %d started on GPU %s", job.jid, self.mapping[rid])
        env = os.environ
        env["CUDA_VISIBLE_DEVICES"] = self.mapping[rid]
        super(GPUResourceManager, self).run(job, rid, exp_config, call_back_func, env=env)

