#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

PyTorch to ONNX
================

Use https://github.com/nerox8664/pytorch2keras for conversion.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.pytorch_to_onnx -i model.pt -o model.onnx \\
       --input_shape 1,3,224,224 --net net.py --net_name Net

"""
from os import path
from typing import List
import torch
from absl import flags, app
from .utils import reset_flag, load_package

FLAGS = flags.FLAGS
reset_flag()

flags.DEFINE_string("model", "model.pt", "input model", short_name="i")
flags.DEFINE_string("output", "model.onnx", "output onnx model", short_name="o")
flags.DEFINE_list("input_shape", "1,3,224,224", "input tensor shape")
flags.DEFINE_string("net", "net.py", "network definition file")
flags.DEFINE_string("net_name", "Net", "class name of the defined network")
flags.register_validator("model", path.isfile, message="missing input model")
flags.register_validator("net", path.isfile, message="missing model definition file")


def convert(model: str, output: str, input_shape: List[int], net_path: str, net_name: str):
    x = torch.randn(*input_shape) # pylint: disable=no-member
    load_package(net_path, net_name)
    model = torch.load(model)
    print("Pytorch model loaded")
    _ = model(x)
    model.eval()

    # Export the model
    torch.onnx.export(model, x, output,
                  input_names = ['input'], output_names = ['output'], 
                  do_constant_folding=True   # whether to execute constant folding for optimization
                  )
    print("Model exported to ONNX")

def _main(_):
    input_shape = [int(i) for i in FLAGS.input_shape]
    convert(FLAGS.model, FLAGS.output, input_shape, FLAGS.net, FLAGS.net_name)


if __name__ == "__main__":
    app.run(_main)
