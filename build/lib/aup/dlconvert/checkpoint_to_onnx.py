#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Checkpoint to ONNX
==================

Additional node tensor names are needed to convert TF checkpoint to ONNX.
See :func:`dlconvert.to_onnx.convert` for more information.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.checkpoint_to_onnx.py --model model_ckpt/ckpt.meta \\
      --output model.onnx \\
      --input_nodes input:0 \\
      --output_nodes output/Softmax:0 \\
      [--input_shape 1,224,224,3]

"""
from os import path
from absl import flags, app
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag() 

from .to_onnx import convert_onnx # pylint: disable=wrong-import-position

flags.DEFINE_string("model", "model_ckpt/ckpt.meta", "input model ckpt meta file path", short_name="i")
flags.DEFINE_string("output", "model.onnx", "output onnx model", short_name="o")
flags.DEFINE_string("input_nodes", "input:0", "model input names (sep by comma)")
flags.DEFINE_string("output_nodes", "label:0", "model output names (sep by comma)")
flags.DEFINE_string("input_shape", None, "input shape")
flags.register_validator("model", path.isfile, message="Input checkpoint meta file is missing")


def convert(model: str, output: str, input_nodes: str, output_nodes: str, input_shape: str):
    """Convert TF checkpoint to ONNX use `tf2onnx <https://github.com/onnx/tensorflow-onnx>`_ package.

    Args:
        model (str): meta file path
        output (str): output onnx filename
        input_nodes (str): model input names
        output_nodes (str): model output names
        [input_shape (str): model input shape, needed if input dimension is not specified in model graph]
    """
    if input_shape is not None:
        # match input_shape with input_node and recreate the input_nodes string
        shapes = []
        input_shapes = FLAGS.input_shape.split(";")
        input_nodes = input_nodes.split(",")
        new_input_nodes = []
        for input_node, input_shape in zip(input_nodes, input_shapes):
            new_input_node = input_node + "[" + input_shape + "]"
            new_input_nodes.append(new_input_node)
        input_nodes = ",".join(new_input_nodes)

    argv = {"checkpoint" : model, 
            "output" : output,
            "inputs" : input_nodes,
            "outputs" : output_nodes}
    convert_onnx(**argv)

def _main(_):
    convert(FLAGS.model, FLAGS.output, FLAGS.input_nodes, FLAGS.output_nodes, FLAGS.input_shape)

if __name__ == "__main__":
    app.run(_main)
