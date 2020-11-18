"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from absl import flags
from os import path, remove
import json
from six import PY2
from tensorflow import __version__ # pylint: disable=no-name-in-module

@unittest.skipIf(PY2, "model conversion does not support python2.x")
class KerasToOnnxTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.h5")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.onnx")
    
    def test_conversion(self):
        flags.FLAGS(['keras_to_onnx.py','-i=%s'%self.model,'-o=%s'%self.output])
        self.k2o._main(None)

    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import keras_to_onnx
        from aup.dlconvert import to_onnx
        import importlib
        importlib.reload(to_onnx)
        cls.k2o = keras_to_onnx
        return super().setUpClass()