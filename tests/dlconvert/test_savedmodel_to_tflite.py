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
class SavedModelToTFLiteTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_savedmodel")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.tflite")
    default = ["savedmodel_to_tflite", "--model=%s" % model, "-o=%s"%output]
    
    @unittest.skipIf(__version__[0] == "1", "IdentityN is not supported in tf1.15, tf2.x is fine")
    def test_conversion_plain(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        flags.FLAGS(self.default)
        self.s2t._main(None)

    def tearDown(self):
        flags.FLAGS.unparse_flags()  # https://github.com/abseil/abseil-py/issues/36
        if path.isfile(self.output):
            remove(self.output)

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import savedmodel_to_tflite
        from aup.dlconvert import to_tflite
        import importlib
        importlib.reload(to_tflite)
        cls.s2t = savedmodel_to_tflite
        return super().setUpClass()
