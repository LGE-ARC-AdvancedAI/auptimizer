"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from absl import flags
from os import path, remove, environ
import json
import tensorflow as tf
from tensorflow import __version__ # pylint: disable=no-name-in-module
import warnings
from six import PY2

tf2test = False
if "TF2TEST" in environ and environ["TF2TEST"]:
    tf2test = True

@unittest.skipIf(PY2 or not tf2test, "Skip for TF2 no eager mode testing.  Use TF2TEST variable to activate tests.")
class SavedModelToOnnxTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_savedmodel")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.onnx")
    
    @unittest.skipIf(__version__[0] == "1", "not supported in tf1.15, tf2.x is fine")
    def test_conversion(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        flags.FLAGS(['savedmodel_to_onnx.py','-i=%s'%self.model,'-o=%s'%self.output])
        self.s2o._main(None)

    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import savedmodel_to_onnx
        from aup.dlconvert import to_onnx
        import importlib
        importlib.reload(to_onnx)
        cls.s2o = savedmodel_to_onnx
        return super().setUpClass()
