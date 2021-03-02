"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from aup.EE.Job import Job
from unittest import TestCase, skipIf
from six import PY2, PY3


# @skipIf(PY2, "BOHB is not supported in Python2")
@skipIf(PY3, "BOHB test not supported in travis environment")
class BOHBTestCase(TestCase):
    config = [{"name": "choice", "range": (1, 2, 3), "type": "choice"},
              {"name": "float", "range": [0, 1], "type": "float"},
              {"name": "int", "range": [1, 10], "type": "int"}]

    def test_create_configspace(self):
        from aup.Proposer import BOHBProposer as bohb
        cs = bohb.BOHBProposer.create_configspace(self.config)
        c = cs.get_hyperparameter('choice')
        self.assertTupleEqual(c.choices, self.config[0]['range'])

        for i in range(10):
            cf = cs.sample_configuration()
            v = cf.get('float')
            self.assertTrue(0 <= v <= 1)
            self.assertIsInstance(v, float)

            v = cf.get('int')
            self.assertTrue(0 <= v <= 10)
            self.assertIsInstance(v, int)

            v = cf.get('choice')
            self.assertTrue(v in (1, 2, 3))

    def test_nsample(self):
        from aup.Proposer import BOHBProposer as bohb
        proposer = bohb.BOHBProposer({"parameter_config":self.config,"target":"min"})
        self.assertEqual(proposer.nSamples, 182)

    def test_param(self):
        from aup.Proposer import BOHBProposer as bohb
        from aup.EE.Job import Job
        proposer = bohb.BOHBProposer({"parameter_config": self.config, "target": "min",
                                      "n_iterations":2, 'max_budget':3})

        for i in range(proposer.nSamples):
            config = proposer.get_param()
            self.assertTrue(0 <= config['float'] <= 1)
            self.assertTrue(0 <= config['int'] <= 10)
            self.assertTrue(config['choice'] in (1,2,3))
            job = Job('.', config)
            proposer.update(0, job)

        self.assertIsNone(proposer.get_param())

    def test_failed(self):
        from aup.Proposer import BOHBProposer as bohb
        proposer = bohb.BOHBProposer({"parameter_config": self.config, "target": "min",
                                      "n_iterations":2, 'max_budget':3})
        try:
            proposer.failed(Job("none", {"tid": 1}))
            self.assertTrue(False)
        except NotImplementedError:
            pass
