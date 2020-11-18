#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Keras to ONNX
=============

Depends on `tf2onnx <https://github.com/onnx/tensorflow-onnx>`_ and
`keras2onnx <https://github.com/onnx/keras-onnx>`_ (TF1.x support only).
Needs to import `tf2onnx` first to resolve dependency
otherwise import `keras2onnx` may result in error

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.keras_to_onnx.py -i model.h5 -o model.onnx

"""
from os import path, environ
environ["TF_KERAS"] = "1"

import tf2onnx
import keras2onnx # pylint: disable=import-error

from absl import flags, app
from tensorflow.compat.v1 import keras # pylint: disable=import-error
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag()

flags.DEFINE_string("model", "model.h5", "input model", short_name="i")
flags.DEFINE_string("output", "model.onnx", "output", short_name="o")
flags.register_validator("model", path.isfile, message="missing input model")


def convert(model: str, output: str):
    """Convert Keras model to ONNX

    Args:
        model (str): Keras h5 model file path
        output (str): output ONNX file path
    """
    model = keras.models.load_model(model)
    model = keras2onnx.convert_keras(model)
    with open(output, "wb") as fp:
        fp.write(model.SerializeToString())


def _main(_):
    convert(FLAGS.model, FLAGS.output)


if __name__ == "__main__":
    app.run(_main)
