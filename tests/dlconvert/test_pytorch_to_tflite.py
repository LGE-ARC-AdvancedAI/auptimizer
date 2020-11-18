"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from absl import flags
from os import path, remove, environ
import json
from six import PY2
from tensorflow import __version__ # pylint: disable=no-name-in-module

tf2test = False
if "TF2TEST" in environ and environ["TF2TEST"]:
    tf2test = True

@unittest.skipIf(PY2 or __version__[0] == "2" and not tf2test, "Skip for TF2 no eager mode testing.  Use TF2TEST variable to activate tests.")
class PytorchToKerasTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.pt")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.tflite")
    default = ["pytorch_to_tflite.py", "--model=%s" % model, "-o=%s"%output]
    
    # @unittest.skipIf(__version__[0] == "1" and tf2test, "TF v1.x doesn't work with TF eager mode in testing")
    @unittest.skipIf(__version__[0] == "1", "test does not pass with TF v1.x")
    def test_conversion(self):
        command = self.default.copy()
        command.extend(["--net=%s"%path.join("tests", "dlconvert", "data","pytorch_model.py"),
                        "--net_name=Net",
                        "--input_shape=1,3,224,224"])
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
                delattr(flags.FLAGS,name)
        from aup.dlconvert import pytorch_to_tflite
        from aup.dlconvert import to_tflite
        import importlib
        importlib.reload(to_tflite)
        cls.p2t = pytorch_to_tflite
        return super().setUpClass()