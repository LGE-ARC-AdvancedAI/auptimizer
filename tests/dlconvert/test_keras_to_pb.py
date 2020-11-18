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

tf2test = False
if "TF2TEST" in environ and environ["TF2TEST"]:
    tf2test = True


@unittest.skipIf(PY2 or tf2test, "skip testing for tf2 environment with eager mode")
class KerasToPBTestCase(unittest.TestCase):
    model = path.join(path.dirname(path.abspath(__file__)), "data", "test_model.h5")
    output = path.join(path.dirname(path.abspath(__file__)), "tmp.pb")

    @classmethod
    def setUpClass(cls):
        names = json.load(open(path.join(path.dirname(path.abspath(__file__)), "data", "flag_names.json")))
        for name in names:
            if name in list(flags.FLAGS):
                delattr(flags.FLAGS,name)
        from aup.dlconvert import keras_to_pb
        cls.k2p = keras_to_pb
        return super().setUpClass()

    def test_conversion(self):
        flags.FLAGS(['keras_to_pb.py','-i=%s'%self.model,'-o=%s'%self.output, '--nofrozen'])
        self.k2p._main(None)

    def test_frozen(self):
        flags.FLAGS(['keras_to_pb.py','-i=%s'%self.model,'-o=%s'%self.output, '--frozen'])
        self.k2p._main(None)

    def tearDown(self):
        if path.isfile(self.output):
            remove(self.output)

