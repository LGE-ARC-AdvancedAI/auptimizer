"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from absl import flags
from os import path, remove, environ
import json
from tensorflow import __version__
from six import PY2

tf2test = False
if "TF2TEST" in environ and environ["TF2TEST"]:
    tf2test = True

@unittest.skipIf(PY2 or tf2test, "skip for tf2 environment with eager mode testing")
class CheckpointToPBTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model_ckpt/ckpt.meta")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.tflite")

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import checkpoint_to_tflite
        cls.c2t = checkpoint_to_tflite
        return super().setUpClass()

    def test_conversion(self):
        flags.FLAGS(['checkpoint_to_tflite.py','-i=%s' % self.model,'-o=%s' % self.output,
                     '--input_nodes=input:0', '--output_nodes=output/Softmax:0'])
        self.c2t._main(None)

    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)
