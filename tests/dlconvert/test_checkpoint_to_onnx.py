"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
import sys
from absl import flags
from os import path, remove
from six import PY2

import json
from tensorflow import __version__  # pylint: disable=no-name-in-module
from tensorflow.python.util import deprecation
deprecation._PRINT_DEPRECATION_WARNINGS = False

@unittest.skipIf(PY2, "model conversion does not support python2.x")
class CheckpointToOnnxTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model_ckpt/ckpt.meta")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.onnx")

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS, name)
        from aup.dlconvert import checkpoint_to_onnx
        cls.c2o = checkpoint_to_onnx

    def test_conversion(self):
        flags.FLAGS(['checkpoint_to_onnx.py','-i=%s' % self.model,'-o=%s' % self.output,
                     "--input_nodes=input:0","--output_nodes=output/Softmax:0"])
        self.c2o._main(None)

    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)
