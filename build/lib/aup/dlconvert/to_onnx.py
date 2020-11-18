"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Convert to ONNX
===============

Based on tf2onnx version>=1.6.0
See `more arguments <https://github.com/onnx/tensorflow-onnx>`_.

"""
import sys
from tf2onnx import convert
from absl import flags

flags.DEFINE_string("opset", "10", "opset version to use for onnx")
FLAGS = flags.FLAGS


def convert_onnx(**kwargs):
    # https://github.com/onnx/tensorflow-onnx
    # sys.argv = ['checkpoint2onnx.py', 
    #             "--inputs", FLAGS.input_nodes,
    #             "--outputs", FLAGS.output_nodes]
    sys.argv = ["convert.py",
                "--opset", FLAGS.opset]
    # add specific arguments for conversions from different source format
    for k, v in kwargs.items():
        sys.argv.extend(["--%s" % k, "%s" % v])
    convert.main()
