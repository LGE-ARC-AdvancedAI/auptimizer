"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest

from aup.EE.Job import Job
from aup.Proposer import HyperbandProposer as hp


class HyperbandTestCase(unittest.TestCase):
    def setUp(self):
        self.pc = {
            "proposer": "spearmint",
            "n_samples": 10,
            "grid_size": 200,
            "target": "min",
            "parameter_config": [
                {"name": "x", "type": "float", "range": [1, 10]},
                {"name": "y", "type": "int", "range": [1, 10]},
                {"name": "z", "type": "choice", "range": [1, 2, 10]}
            ]
        }

    def test_hp(self):
        p = hp.HyperbandProposer(self.pc)
        for j in range(3):
            tid = []
            for i in range(100):
                v = p.get()
                if v:
                    tid.append(v['tid'])
            for i in tid:
                job = Job("none", {"tid": i})
                p.update(0.1, job)

        self.assertRaises(NotImplementedError, p.save, '')
        self.assertRaises(NotImplementedError, p.reload, '')

    def test_hp_min(self):
        self.pc['target'] = 'max'
        p = hp.HyperbandProposer(self.pc)
        for j in range(6):
            tid = []
            for i in range(100):
                v = p.get()
                if v:
                    tid.append(v['tid'])
            for i in tid:
                job = Job("none", {"tid": i})
                p.update(0.1, job)

    def test_no_implemented(self):
        self.pc['parameter_config'][0]['name'] = 'tid'
        self.assertRaises(KeyError, hp.HyperbandProposer, self.pc)
        
    def test_failed(self):
        p = hp.HyperbandProposer(self.pc)
        try:
            p.failed(Job("none", {"tid": 1}))
            self.assertTrue(False)
        except NotImplementedError:
            pass


if __name__ == '__main__':
    unittest.main()
