"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import unittest

from aup import convert as ac


class AutoConvertTestCase(unittest.TestCase):
    exp = os.path.join("tests", "data", "exp4.json")
    script = os.path.join("tests", "data", "task4.py")

    def test_get_param(self):
        self.assertListEqual(['x'], ac.get_param(self.exp))
        exp = os.path.join("tests", "data", "exp4_no_param.json")
        self.assertRaises(KeyError, ac.get_param, exp)
        exp = os.path.join("tests", "data", "exp4_no_name.json")
        self.assertRaises(KeyError, ac.get_param, exp)

    def test_get_output(self):
        self.assertEqual("to_delete.py", ac.get_output_name(self.exp))
        exp = os.path.join("tests", "data", "exp4_no_script.json")
        self.assertRaises(KeyError, ac.get_output_name, exp)

    def test_modification(self):
        with open(self.script,'r') as f:
            script = f.read()
        script = ac.add_shenbang(script)
        self.assertEqual(script[:2], "#!")

        script = ac.add_func(script, "function", ['x'])
        script = ac.add_main(script)
        self.assertTrue("__main__" in script)
        self.assertTrue(ac.add_main(script))


if __name__ == '__main__':
    unittest.main()
