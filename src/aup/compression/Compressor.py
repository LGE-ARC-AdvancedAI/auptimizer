"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import copy
import logging
import os
logger = logging.getLogger(__name__)
COMPRESSORS = {}

try:
    from .tensorflow import pruning as tf_pruning

    COMPRESSORS.update({
        "tensorflow": {
            "pruning": {
                "level": tf_pruning.LevelPruner,
            }
        },
    })
except (ImportError, AssertionError) as ex:
    logger.warning("Error when importing Tensorflow 2.X for compression: {}".format(ex))

try:
    from .torch import pruning as torch_pruning
    from .torch import quantization as torch_quantization
    from .torch import ModelSpeedup, apply_compression_results
    from .torch.utils.counter import count_flops_params
    import torch
    
    COMPRESSORS.update({
        "torch": {
            "pruning": {
                "agp": torch_pruning.AGPPruner,
                "admm": torch_pruning.ADMMPruner,
                "auto_compress": torch_pruning.AutoCompressPruner,
                "lottery_ticket": torch_pruning.LotteryTicketPruner,
                "level": torch_pruning.LevelPruner,
                "slim": torch_pruning.SlimPruner,
                "l1_filter": torch_pruning.L1FilterPruner,
                "l2_filter": torch_pruning.L2FilterPruner,
                "fpgm": torch_pruning.FPGMPruner,
                "net_adapt": torch_pruning.NetAdaptPruner,
                "sensitivity": torch_pruning.SensitivityPruner,
                "simulated_annealing": torch_pruning.SimulatedAnnealingPruner,
                "amc": torch_pruning.AMCPruner,
                "taylor_fo_weight_filter": torch_pruning.TaylorFOWeightFilterPruner,
                "activation_apoz_rank_filter": torch_pruning.ActivationAPoZRankFilterPruner,
                "activation_mean_rank_filter": torch_pruning.ActivationMeanRankFilterPruner,
            },
            "quantization": {
                "naive": torch_quantization.NaiveQuantizer,
                "qat": torch_quantization.QAT_Quantizer,
                "dorefa": torch_quantization.DoReFaQuantizer,
                "bnn": torch_quantization.BNNQuantizer,
            }
        }
    })
except ImportError as ex:
    logger.warning("Error when importing PyTorch for compression: {}".format(ex))

from ..utils import check_missing_key


def create_compressor(model, config, *args, **kwargs):
    """
    Helper function for user scripts to generate a compression object

    :param model: Model to compress
    :param config: Compressor configuration
    """
    logging.basicConfig(format="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")  
    c_framework = config["compression_framework"]
    c_type = config["compression_type"]
    c_str = config["compressor"]
    logger.info("Creating compressor: framework={} type={} compressor={}".format(
        c_framework, c_type, c_str))

    if c_framework not in COMPRESSORS:
        raise ValueError(("Compression framework \"{}\" not recognized. Supported frameworks for installed packages: {}\n" +
                          "Please check messages above, it is possible that an import error lead to this situation.").format(
            c_framework, ", ".join(COMPRESSORS.keys())))
    if c_type not in COMPRESSORS[c_framework]:
        raise ValueError("Compression type \"{}\" not recognized for framework \"{}\". Supported types: {}".format(
            c_type, c_framework, ", ".join(COMPRESSORS[c_framework].keys())))
    if c_str not in COMPRESSORS[c_framework][c_type]:
        raise ValueError("Compressor \"{}\" not recognized for framework \"{}\" and type \"{}\". Supported compressors: {}".format(
            c_str, c_framework, c_type, ", ".join(COMPRESSORS[c_framework][c_type].keys())))

    # Check if all op_names can be found in model 
    if c_framework == "torch":
        layer_names = {".".join(key.split(".")[:-1]) for key in model.state_dict().keys()}
    elif c_framework == "tensorflow":
        layer_names = {layer.name for layer in model.layers}
    else:
        raise NotImplementedError
    for config_item in config["config_list"]:
        if "op_names" in config_item:
            for op_name in config_item["op_names"]:
                if op_name not in layer_names:
                    raise ValueError("op_name \"{}\" not found in model. Ops found: {}".format(op_name, layer_names))

    nni_compressor = COMPRESSORS[c_framework][c_type][c_str](model=model, config_list=config["config_list"], *args, **kwargs)
    
    compressor = Compressor(model, nni_compressor, c_framework, c_type, c_str)

    return compressor


class Compressor:
    def __init__(self, model, nni_compressor, c_framework, c_type, c_str):
        self._nni_compressor = nni_compressor
        self._compression_framework = c_framework
        self._compression_type = c_type
        self._compressor_str = c_str
        self._applied_speedup = False
        self.model = model
    
    def compress(self, *args, **kwargs):
        return self._nni_compressor.compress(*args, **kwargs)

    def update_epoch(self, epoch):
        return self._nni_compressor.update_epoch(epoch)
    
    def step(self):
        return self._nni_compressor.step()
    
    def get_prune_iterations(self):
        return self._nni_compressor.get_prune_iterations()
    
    def prune_iteration_start(self):
        return self._nni_compressor.prune_iteration_start()

    def apply_speedup(self, dummy_input, mask_path=None, *args, **kwargs):
        if self._compression_framework != "torch" or \
           self._compression_type != "pruning":
            raise ValueError("Can only apply_speedup for PyTorch pruning compressions.") 

        # Ideally, inference model would be re-created here, but _unwrap_model() seems to work as well 
        self._nni_compressor._unwrap_model()
        
        try:
            # Normally, the model would be exported first and its masks file used for speedup ("else" case)
            # But here ("if"), the mask_dictionary object is constructed on-demand in-memory without saving to disk
            if mask_path is None:
                mask_dict = self._nni_compressor.get_mask_dict()
                m_speedup = ModelSpeedup(self.model, dummy_input, masks=mask_dict)
            else:
                m_speedup = ModelSpeedup(self.model, dummy_input, masks_file=mask_path)
            m_speedup.speedup_model()
        except Exception as ex:
            self._nni_compressor._wrap_model()
            raise ValueError("Error encountered in apply_speedup.")

        self._applied_speedup = True

        return self.model

    def count_flops_params(self, *args, **kwargs):
        if not self._applied_speedup:
            self._nni_compressor._unwrap_model()
        
        ret = count_flops_params(self.model, *args, **kwargs)
        
        if not self._applied_speedup:
            self._nni_compressor._wrap_model()
        
        return ret

    def export_model(self, model_path, mask_path=None, folder_name=".", speedup=False, dummy_input=None, *args, **kwargs):
        model = self.model
        os.makedirs(folder_name, exist_ok=True)
        model_path = os.path.join(folder_name, model_path)
        if mask_path is not None:
            mask_path = os.path.join(folder_name, mask_path)
        if self._compression_framework == "torch":
            if self._compression_type == "pruning":
                self._nni_compressor.export_model(model_path, mask_path)
                if speedup and not self._applied_speedup:
                    if dummy_input is None:
                        logger.warning("Missing required parameter \"dummy_input\" for speed-up, " +
                                       "saving compressed model without speed-up.")
                    else:
                        try:
                            model = self.apply_speedup(dummy_input, mask_path)
                        except ValueError:
                            logger.warning("Error encountered when applying speed-up, " + 
                                        "saving compressed model without speed-up.")
            torch.save(model.state_dict(), model_path)
        elif self._compression_framework == "tensorflow":
            self.model.save(model_path)
