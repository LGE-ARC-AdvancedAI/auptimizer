#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

PyTorch to Keras
================

Use https://github.com/nerox8664/pytorch2keras for conversion.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.pytorch_to_keras -i model.pt -o model.h5 \\
       --input_shape 1,3,224,224 --net net.py --net_name Net

"""
import tf2onnx # to resolve import error of pytorch2keras
from pytorch2keras import pytorch_to_keras
from typing import List
from os import path
import torch
from absl import flags, app
from .utils import reset_flag, load_package

FLAGS = flags.FLAGS
reset_flag()

flags.DEFINE_string("model", "model.pt", "input model", short_name="i")
flags.DEFINE_string("output", "model.h5", "output keras model", short_name="o")
flags.DEFINE_list("input_shape", "1,3,224,224", "input tensor shape")
flags.DEFINE_string("net", "net.py", "network definition file")
flags.DEFINE_string("net_name", "Net", "class name of the defined network")
flags.register_validator("model", path.isfile, message="missing input model")
flags.register_validator("net", path.isfile, message="missing model definition file")


def convert(model: str, output: str, input_shape: List[int], net_path, net_name):
    """Convert PyTorch model to Keras model
    
    Args:
        model (str): PyTorch model file path
        output (str): output file name for Keras model
        input_shape (List[int]): Tensor shape for input
        net_path ([type]): Python script defines the model
        net_name ([type]): PyTorch model class in the `net_path` file.
    """
    x = torch.randn(*input_shape, requires_grad=True) # pylint: disable=no-member
    load_package(net_path, net_name)
    model = torch.load(model)
    k_model = pytorch_to_keras(model, x, [input_shape[1:]], verbose=False)

    # Export the model
    k_model.save(output)


def _main(_):
    input_shape = [int(i) for i in FLAGS.input_shape]
    convert(FLAGS.model, FLAGS.output, input_shape, FLAGS.net, FLAGS.net_name)


if __name__ == "__main__":
    app.run(_main)