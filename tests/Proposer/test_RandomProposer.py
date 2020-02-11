"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest

import os
import tempfile

from aup.Proposer import RandomProposer as rp


class MyTestCase(unittest.TestCase):
    def test_random_int(self):
        d = [1, 10]
        all_opt = set(range(1, 11))
        f = rp._random_int(d)
        t = set(f() for _ in range(10000))
        self.assertSetEqual(all_opt, t, "Low chance to miss numbers")
        self.assertRaises(ValueError, rp._random_int, [1, 2, 3])

    def test_random_float(self):
        d = [-10, 10]
        f = rp._random_float(d)
        for i in range(100):
            v = f()
            self.assertLessEqual(v, d[1])
            self.assertLessEqual(d[0], v)
        self.assertRaises(ValueError, rp._random_float, [1, 2, 3])

    def test_random_choice(self):
        d = [str(i) for i in range(10)]
        f = rp._random_choice(d)
        for i in range(100):
            self.assertIn(f(), d)

        self.assertRaises(ValueError, rp._random_choice, [])

    def test_init(self):
        config = {}
        self.assertRaises(KeyError, rp.RandomProposer, config)
        config['n_samples'] = 10
        self.assertRaises(KeyError, rp.RandomProposer, config)
        config['parameter_config'] = [{}]
        self.assertRaises(KeyError, rp.RandomProposer, config)
        config['parameter_config'] = [{"name": "a"}]
        self.assertTrue(rp.RandomProposer(config))

    def test_save_restore(self):
        config = {'n_samples': 10, 'parameter_config': [{'name': 'x'}]}
        m = rp.RandomProposer(config)
        path = tempfile.mkdtemp()
        self.assertIn(m.get_param()['x'], [0, 1])

        sav = os.path.join(path, 'test.pkl')
        m.save(sav)
        n = rp.RandomProposer(config)
        n.reload(sav)
        self.assertIn(n.get_param()['x'], [0, 1])
        os.remove(sav)
        os.rmdir(path)

    def test_reset(self):
        config = {'n_samples': 10, 'random_seed': 10, 'parameter_config': [{'name': 'x', 'type': 'int'}]}
        m = rp.RandomProposer(config)

        for i in range(10):
            m.get()
        v = m.get()
        self.assertIs(v, None)
        m.reset()
        self.assertIn(m.get()['x'], [0, 1])
        self.assertEqual(m.counter, 1)


if __name__ == '__main__':
    unittest.main()
