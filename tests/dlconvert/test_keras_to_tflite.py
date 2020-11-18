"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from absl import flags
from os import path, remove, environ
import json
import warnings
import tensorflow as tf
from six import PY2
from tensorflow import __version__ # pylint: disable=no-name-in-module

tf2test = False
if "TF2TEST" in environ and environ["TF2TEST"]:
    tf2test = True

@unittest.skipIf(PY2 or not tf2test, "Skip for TF2 no eager mode testing.  Use TF2TEST variable to activate tests.")
class KerasToTFLiteTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.h5")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.tflite")
    default = ["keras_to_tflite", "--model=%s" % model, "-o=%s"%output]

    def test_conversion_plain(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        flags.FLAGS(self.default)
        self.k2t._main(None)

    def test_conversion_tf16(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        command = self.default.copy()
        command.extend(["--opt=default", "--type=float16"])
        flags.FLAGS(command)
        self.k2t._main(None)

    def test_conversion_uint(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        command = self.default.copy()
        command.extend(["--opt=default", "--type=uint8", "--ops=tflite"])
        flags.FLAGS(command)
        self.k2t._main(None)

    def test_conversion_int8(self):
        if __version__[0] == "2" and not tf.executing_eagerly():
            warnings.warn("TF2.0 not in eager mode, cannot test.")
            return
        command = self.default.copy()
        command.extend(["--opt=default","--type=int8", "--ops=tflite", 
                        "--load=%s"%path.join("tests", "dlconvert", "data", "repdata.py")])
        
        flags.FLAGS(command)
        self.k2t._main(None)

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
        from aup.dlconvert import keras_to_tflite
        cls.k2t = keras_to_tflite
        return super().setUpClass()