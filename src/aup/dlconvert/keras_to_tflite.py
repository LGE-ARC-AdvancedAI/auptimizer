#!/usr/bin/env python3
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Keras to TFlite
===============

See :func:`dlconvert.to_tflite.setup_converter` for more control arguments for `tflite`.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.keras_to_tflite.py --model model.h5 \\
       --output model_keras.tflite \\
       [--load rep_data] \\
       [--opt default --ops int8 --type int8]

"""
from os import path
from tensorflow import lite, keras, __version__ # pylint: disable=no-name-in-module
from absl import flags, app
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag()

from .to_tflite import create_converter # pylint: disable=wrong-import-position

flags.DEFINE_string("model", "model.h5", "input model", short_name="i")
flags.DEFINE_string("output", "model.tflite", "output", short_name="o")
flags.register_validator("model", path.isfile, message="missing input model")


def model_loader(filename: str) -> lite.TFLiteConverter:
    """TF 1/2 tflite converter loading function

    Args:
        filename (str): Keras model file

    Returns:
        lite.TFLiteConverter: TFLite converter to be used
    """
    if __version__[0] == "2":
        model = keras.models.load_model(filename)
        return lite.TFLiteConverter.from_keras_model(model)
    return lite.TFLiteConverter.from_keras_model_file(filename)


def convert(model: str, output: str):
    """Convert Keras model to tflite model

    Args:
        model (str): input model file name
        output (str): output model file name
    """
    converter = create_converter(model, model_loader)
    tflite_model = converter.convert()
    with open(output, "wb") as f:
        f.write(tflite_model)   


def _main(_):
    convert(FLAGS.model, FLAGS.output)


if __name__ == "__main__":
    app.run(_main)
