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

@unittest.skipIf(PY2 or tf2test, "Skip for TF2 eager mode testing.  Unset TF2TEST variable to activate tests.")
class PBToTFLiteTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.pb")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.tflite")
    default = ["pb_to_tflite", "--model=%s" % model, "-o=%s"%output,
               "--input_nodes=input:0", "--output_nodes=output/Softmax:0"]

    def test_conversion_plain(self):
        flags.FLAGS(self.default)
        self.p2t._main(None)

    def test_conversion_tf16(self):
        command = self.default.copy()
        command.extend(["--opt=default","--type=float16"])
        flags.FLAGS(command)
        self.p2t._main(None)

    def test_conversion_uint(self):
        command = self.default.copy()
        command.extend(["--opt=default","--type=uint8", "--ops=tflite"])
        flags.FLAGS(command)
        self.p2t._main(None)

    def test_conversion_int8(self):
        command = self.default.copy()
        command.extend(["--opt=default","--type=int8", "--ops=tflite", 
                        "--load=%s"%path.join("tests", "dlconvert", "data", "repdata.py")])
        
        flags.FLAGS(command)
        self.p2t._main(None)

    def tearDown(self):
        flags.FLAGS.unparse_flags()  # https://github.com/abseil/abseil-py/issues/36
        if path.isfile(self.output):
            remove(self.output)
    
    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS, name)
        from aup.dlconvert import pb_to_tflite
        from aup.dlconvert import to_tflite
        import importlib
        importlib.reload(pb_to_tflite)
        importlib.reload(to_tflite)
        cls.p2t = pb_to_tflite
        return super().setUpClass()
