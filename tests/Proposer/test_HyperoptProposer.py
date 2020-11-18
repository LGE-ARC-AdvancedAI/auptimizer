"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest

import os
import tempfile

from aup.EE.Job import Job
from aup.Proposer import HyperoptProposer as hp


class HyperOptTestCase(unittest.TestCase):
    def setUp(self):
        self.pc = {
            "proposer": "hyperopt",
            "n_samples": 10,
            "engine": "tpe",
            "target": "min",
            "parameter_config": [
                {"name": "x", "range": [0, 1], "type": "int"},
                {"name": "y", "range": [0, 1.], "type": "float"},
                {"name": "z", "range": [0, 1.], "type": "choice"}

            ]
        }

    def test_init(self):
        hp.HyperoptProposer(self.pc)
        self.pc['parameter_config'][0]['type'] = 'wrong'
        self.assertRaises(KeyError, hp.HyperoptProposer, self.pc)
        self.pc['parameter_config'][0]['type'] = 'float'

    def test_verify_config(self):
        self.pc['parameter_config'][0]['name'] = 'tid'
        self.assertRaises(KeyError, hp.HyperoptProposer, self.pc)

    def test_runtime(self):
        p = hp.HyperoptProposer(self.pc)
        c = p.get()
        job = Job("none", c)
        p.update(0.1, job)
        job.config['tid'] = -100
        self.assertRaises(KeyError, p.update, 0.0, job)
        path = tempfile.mkdtemp()
        sav = os.path.join(path, "save.pkl")
        p.save(sav)
        idx = p.counter
        p = hp.HyperoptProposer(self.pc)
        self.assertNotEqual(idx, p.counter)
        p.reload(sav)
        self.assertEqual(idx, p.counter)
        os.remove(sav)
        os.rmdir(path)

    def test_failed(self):
        p = hp.HyperoptProposer(self.pc)
        c = p.get()
        job = Job("none", c)
        p.failed(job)

if __name__ == '__main__':
    unittest.main()
