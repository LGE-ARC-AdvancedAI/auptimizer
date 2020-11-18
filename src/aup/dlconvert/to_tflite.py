"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Convert to TFLite
=================

There are four major control parameters for tflite runtime, see :func:`.setup_tfconverter`.

The data feeding function (`data_fun`) is loaded by `--load`, where the argument is the Python filename defining
`get_data()` to `generate data <https://www.tensorflow.org/lite/performance/post_training_integer_quant#convert_using_quantization>`_ for `int8` quantization. 
Combine with `--undefok` flag to pass more control arguments.

"""
import logging
from os import path, environ
environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  #disable tensorflow debugging messages
from typing import Callable
import numpy as np
from absl import flags
from tensorflow import lite


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

try:
    from tensorflow import enable_eager_execution  # pylint: disable=no-name-in-module

    enable_eager_execution()
except Exception:  # pylint: disable=broad-except
    logger.fatal("Compatibility issue with TF eager execution. Tweak with caution.")

try:
    from tensorflow.lite.python import lite_constants
except ImportError:
    from tensorflow.lite import constants as lite_constants

flags.DEFINE_string("opt", "none", "optimization")
flags.DEFINE_string("type", "float", "data type after quantization")
flags.DEFINE_string("ops", "tflite", "operation set to be used for quantization")
# -- optional for representative data
flags.DEFINE_string("load", "", "use representative data defined in additional python file", short_name="d")

# when using quantization, OPT_ARGS needs to be set to "default"
OPT_ARGS = {
    "default": [lite.Optimize.DEFAULT],
    "none": [],
}
flags.register_validator("opt", lambda x: x in OPT_ARGS, "Keyword not recognized, choose from %s" % OPT_ARGS.keys())

OPS_ARGS = {
    "int8": [lite.OpsSet.TFLITE_BUILTINS_INT8],
    "tflite": [lite.OpsSet.TFLITE_BUILTINS],  # default
    "tf": [lite.OpsSet.SELECT_TF_OPS, lite.OpsSet.TFLITE_BUILTINS],
}
flags.register_validator("ops", lambda x: x in OPS_ARGS, "Keyword not recognized, choose from %s" % OPS_ARGS.keys())

TYPE_ARGS = {
    "float": [lite_constants.FLOAT],  # tf.float32, default
    "int8": [lite_constants.INT8],  # tf.int8
    "float16": [lite_constants.FLOAT16],  # tf.float16 -> tensorflow>=1.15
    "uint8": [lite_constants.QUANTIZED_UINT8],  # tf.uint
}
flags.register_validator("type", lambda x: x in TYPE_ARGS, "Keyword not recognized, choose from %s" % TYPE_ARGS.keys())
FLAGS = flags.FLAGS


def setup_tfconverter(
    converter: lite.TFLiteConverter, dtype: str, opt: str, ops: str, data_fun: Callable = None
) -> lite.TFLiteConverter:
    """Setup control arguments for `TFLiteConverter <https://www.tensorflow.org/lite/convert>`_
    
    Args:
        converter (lite.TFLiteConverter): loaded `TFLiteConverter`.
        dtype (str): data types: `float`, `float16`, `int8`, `uint8`.
        opt (str): optimization: `none` for `float`, `default` for ther data types.
        ops (str): operation sets: `tflite`, `tf`, `int8`.
        data_fun (Callable, optional): [description]. Defaults to None.
    
    Returns:
        lite.TFLiteConverter: `TFLiteConverter` with additional arguments set up.
    """

    if data_fun:
        converter.representative_dataset = data_fun
    converter.optimizations = OPT_ARGS[opt]
    converter.target_spec.supported_ops = OPS_ARGS[ops]
    converter.target_spec.supported_types = TYPE_ARGS[dtype]
    return converter


def create_converter(model: str, model_loader: Callable[[str], lite.TFLiteConverter]) -> lite.TFLiteConverter:
    """Setup the TFLite converter

    Args:
        model (str): model filename
        model_loader (Callable[[str], lite.TFLiteConverter]): function to load model file and return a `TFLiteConverter`

    Returns:
        lite.TFLiteConverter: `TFLiteConverter` with additional arguments set up.

    """
    if FLAGS.type != "float":
        assert FLAGS.opt != "none", "--opt=default is required for quantization."
    else:
        assert FLAGS.opt == "none", "--opt=none is required for float32 operation."

    converter = model_loader(model)
    if FLAGS.load:
        try:
            import sys, importlib

            sys.path.insert(0, path.dirname(path.abspath(FLAGS.load)))
            mod = path.basename(FLAGS.load).rstrip(".py")
            mod = importlib.import_module(mod)
            get_dataset = getattr(mod, "get_dataset")
        except Exception as error:  # pragma: no cover
            logger.fatal("Failed to import get_dataset from %s.py", FLAGS.load)
            raise error
        data = get_dataset()

        def data_gen():
            for i in data:
                yield [i[0].numpy().astype(np.float32)]

    else:
        data_gen = None
    return setup_tfconverter(converter, FLAGS.type, FLAGS.opt, FLAGS.ops, data_gen)
