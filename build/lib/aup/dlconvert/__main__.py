"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

DLconvert main entry
====================

Convert models to TFLite/ONNX format for deployment.

.. code-block:: bash

   $ python -m aup.dlconvert -f <conversion_json_file> \\


Support frameworks and model formats are:

+ Keras `.h5`
+ Keras `.hdf5`
+ Savedmodel (directory)
+ PyTorch `.pt`
+ TF ProtoBuf `.pb`
+ Checkpoint `.meta`
+ TFLite `.tflite`
+ ONNX `.onnx`

"""
import argparse
import os
import sys
import json

import logging
import coloredlogs
import subprocess

from ..utils import LOG_LEVEL

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  #disable tensorflow debugging messages
logger = logging.getLogger("aup.dlconvert")



MODEL_MAP = {"h5":"keras",
             "tflite":"tflite",
             "onnx":"onnx",
             "pb":"pb",
             "hdf5":"keras",
             "pt":"pytorch",
             "meta":"checkpoint"}


def _verify_file(filename):
    assert len(filename) >= 2, "Filename should be <x>.<type>"
    assert filename.split(".")[-1] in MODEL_MAP, "unsupport file type for %s"%filename

    
def run_conversion(model, output, unknownargs):
    if os.path.isdir(model):
        from_model = "savedmodel"
    else:
        from_model = MODEL_MAP[model.split(".")[-1]]
      
    to_model = MODEL_MAP[output.split(".")[-1]]
    func_to_call = "aup.dlconvert.%s_to_%s -i %s -o %s"%(from_model, to_model, model, output)
    command = sys.executable + " -m " + func_to_call + " " + " ".join(unknownargs)
    logger.info("Running: " + command)

    proc = subprocess.Popen([command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    (out, err) = proc.communicate()
    logger.debug("Conversion debug details:" + str(out))
    logger.debug("Conversion debug errors:" + str(err))
    success_code = proc.returncode
    if success_code == 0:
        logger.info("Conversion Success: " + output)
    else:
        raise Exception("Conversion Failed")
    
    
def get_parameters(job):
    if not job['convert_from'] or not job['convert_to']:
        logging.critical("The job does not have correct file details. Please provide a 'convert_from' and 'convert_to' parameters.")
        return (None, None, None) 
    model = job["convert_from"]
    output = job["convert_to"]
    skip = False #for testing purposes only, skipping the model the user does not want to convert
    unknownargs = {}
    if "skip" in job:
        skip = (job["skip"]=="True")
        if skip:
            return(model, output, skip, [])

    if "input_nodes" in job:
        unknownargs["input_nodes"] = job["input_nodes"]
        
    if "output_nodes" in job:
        unknownargs["output_nodes"] = job["output_nodes"]
        
    if "network_script" in job:
        unknownargs["net"] = job["network_script"]
        
    if "network_name" in job:
        unknownargs["net_name"] = job["network_name"]
        
    if "input_shape" in job:
        unknownargs["input_shape"] = job["input_shape"]
        
    if "frozen" in job:
        unknownargs["frozen"] = job["frozen"]
        
    if "onnx_opset" in job:
        unknownargs["opset"] = job["onnx_opset"]
        
    if "savedmodel_tag" in job:
        unknownargs["tag"] = job["savedmodel_tag"]
        
    if "savedmodel_signature" in job:
        unknownargs["signature"] = job["savedmodel_signature"]
        
    if "quantization" in job:
        if "optimization" in job["quantization"]:    
            unknownargs["opt"] = job["quantization"]["optimization"]
        if "type" in job["quantization"]:
            unknownargs["type"] = job["quantization"]["type"]
        if "opsset" in job["quantization"]:
            unknownargs["ops"] = job["quantization"]["opsset"]
        if "load" in job["quantization"]:
            unknownargs["load"] = job["quantization"]["load"]
            
    other_args = []
    if ".onnx" in output and "opt" in unknownargs:
        unknownargs.pop("opt")
        
    for key in unknownargs:
        other_args.append("--"+key+" "+unknownargs[key]+" ")
            
    return(model, output, skip, other_args)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=False, help="Input conversion json file")
    parser.add_argument("-d", "--dic", required=False, help="Input conversion json dictionary")
    parser.add_argument("--log", default="info", required=False, choices=["debug", "info", "warn", "error"], help="log level")
    args, unknownargs = parser.parse_known_args()
    
    coloredlogs.install(level=LOG_LEVEL[args.log], fmt="%(name)s - %(levelname)s - %(message)s")
    
    if args.file:
        try:
            with open(args.file) as f:
                convert_dict = json.load(f)
        except Exception as e:
            logging.fatal("The json file could not be converted")
            raise e
    elif args.dic:
        try:
            convert_dict = json.loads(args.dic)
        except Exception as e:
            logging.fatal("The json dictionary could not be converted")
            raise e
    else:
        logging.fatal("The json file or dictionary not provided")
        convert_dict={}

    for job in convert_dict:
        try:
            (model, output, skip, unknownargs) = get_parameters(job)
            if not skip:
                logger.info("current job: " + str(job))
                run_conversion(model, output, unknownargs)
        except:
            logging.fatal("The following conversion job failed: " + str(job))
            continue
         

