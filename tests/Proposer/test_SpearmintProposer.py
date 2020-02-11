"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest

import os
import shutil
from six import PY3

from aup.EE.Job import Job
from aup.Proposer import SpearmintProposer as sp


@unittest.skipIf(PY3, "Spearmint has some issue with Python3")
class SpearmintTestCase(unittest.TestCase):
    def setUp(self):
        self.pc = {
            "proposer": "spearmint",
            "n_samples": 100,
            "grid_size": 200,
            "target": "min",
            "parameter_config": [
                {"name": "x", "type": "float", "range": [1, 10]},
                {"name": "y", "type": "int", "range": [1, 10]},
                {"name": "z", "type": "choice", "range": [1, 2, 10]}
            ]
        }
        self.path = os.path.join("tests", "tmp_tests")
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.mkdir(self.path)
        self.pc['workingdir'] = self.path

    def tearDown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    def test_init(self):
        pc = self.pc.copy()
        pc['engine'] = "wrong"
        self.assertRaises(KeyError, sp.SpearmintProposer, pc)

        pc = self.pc.copy()
        pc['parameter_config'][0]['size'] = 2
        p = sp.SpearmintProposer(pc)
        self.assertRaises(NotImplementedError, p.get)

        pc = self.pc.copy()
        pc['parameter_config'][0]['name'] = 'job_id'
        self.assertRaises(ValueError, sp.SpearmintProposer, pc)

    def test_get(self):
        p = sp.SpearmintProposer(self.pc)
        for j in range(3):
            tid = []
            for i in range(10):
                v = p.get()
                tid.append(v['job_id'])
            for i in tid:
                job = Job("none", {'job_id': i})
                p.update(1, job)
        self.assertTrue(True)
        self.assertTrue(sp.SpearmintProposer(self.pc))

    def test_finish(self):
        p = sp.SpearmintProposer(self.pc)
        self.assertRaises(NotImplementedError, p.save, "")
        self.assertRaises(NotImplementedError, p.reload, "")


if __name__ == '__main__':
    unittest.main()
