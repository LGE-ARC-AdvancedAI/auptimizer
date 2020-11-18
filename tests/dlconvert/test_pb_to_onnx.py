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
class PBToOnnxTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.pb")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.onnx")

    @classmethod
    def setUpClass(cls):
        from aup.dlconvert import to_onnx # reload inner package
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import pb_to_onnx
        
        import importlib
        importlib.reload(to_onnx)
        cls.p2o = pb_to_onnx
        return super().setUpClass()

    def test_conversion(self):
        flags.FLAGS(['pb_to_onnx.py','-i=%s'%self.model,'-o=%s'%self.output, "--input_nodes=input:0","--output_nodes=output/Softmax:0"])
        self.p2o._main(None)


    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)
