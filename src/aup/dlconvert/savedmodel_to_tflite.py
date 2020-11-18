#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

SavedModel to tflite
====================

*Based on the version of ops, it may fail.*

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.savedmodel_to_tflite.py --model model/ \\
       --output model_keras.tflite \\
       [--load rep_data] \\
       [--opt default --ops int8 --type int8]

"""
from os import path, environ
environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  #disable tensorflow debugging messages

from tensorflow import lite, keras, saved_model
from absl import flags, app
from .utils import reset_flag

import logging
import coloredlogs
from ..utils import LOG_LEVEL
logger = logging.getLogger("aup.dlconvert")

FLAGS = flags.FLAGS
reset_flag()

from .to_tflite import create_converter # pylint: disable=wrong-import-position

flags.DEFINE_string("model", "model", "input model path", short_name="i")
flags.DEFINE_string("output", "model.tflite", "output", short_name="o")
flags.register_validator("model", path.isdir, message="missing input model")


def model_loader(foldername:str) -> lite.TFLiteConverter:
    """Function to load model file into `TFLiteConverter`.
    
    Args:
        foldername (str): file name
    
    Returns:
        lite.TFLiteConverter: TFLiteConverter to create tflite model
    """
    return lite.TFLiteConverter.from_saved_model(foldername)


def _main(_):
    # cannot convert savedmodel with empty SignatureMap
    model = saved_model.load(FLAGS.model)
    if len(model.signatures) == 0:
        logger.info("Savedmodel cannot be converted with empty signature map! Please check model.signatures before conversion.")
        raise ValueError

    converter = create_converter(FLAGS.model, model_loader)
    tflite_model = converter.convert()
    with open(FLAGS.output, "wb") as f:
        f.write(tflite_model)

if __name__ == "__main__":
    app.run(_main)

    
    

