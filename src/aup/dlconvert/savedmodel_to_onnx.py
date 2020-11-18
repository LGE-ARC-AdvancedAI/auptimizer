#!/usr/bin/env python

"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

SavedModel to ONNX
==================

**Not working**

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.savedmodel_to_onnx.py --model savedModel/ --output model.onnx

"""
from os import path
from absl import flags, app
from .utils import reset_flag
import logging

logger = logging.getLogger(__name__)
FLAGS = flags.FLAGS
reset_flag()
from .to_onnx import convert_onnx # pylint: disable=wrong-import-position

flags.DEFINE_string("model", "saved_model", "input savedmodel folder path", short_name="i")
flags.DEFINE_string("output", "model.onnx", "output onnx model", short_name="o")
flags.DEFINE_string("tag", "serve", "tag to use for saved_model")
flags.DEFINE_string("signature", "serving_default", "signature to use from saved_model")
flags.DEFINE_string("concrete_function", None, "For TF2.x saved_model, index of func signature in __call__ (--signature_def is ignored)")
flags.register_validator("model", path.isdir, message="missing input model")


def convert(model: str, output: str, tag: str, signature: str, concrete_function: str):
    """Convert TF SavedModel to ONNX (currently only support TF2 and TF2 SavedModels)

    Args:
        model (str): TF SavedModel folder path
        output (str): ONNX output filename
        tag (str, optional): tag to use for SavedModel, default is "serve"
        signature (str, optional): signature to use for SavedModel, default is "serving_default"
        concrete_function (str, optional): index of func signature in __call__ to use instead of signature], default is None
    """
    if model[-1] != "/":
        model += "/"
    argv = {"saved-model" : model, 
            "output" : output,
            "tag" : tag,
            "signature_def" : signature}
    if concrete_function is not None:
        argv["concrete_function"] = concrete_function
    
    convert_onnx(**argv)


def _main(_):
    convert(FLAGS.model, FLAGS.output, FLAGS.tag, FLAGS.signature, FLAGS.concrete_function)

if __name__ == "__main__":
    app.run(_main)
