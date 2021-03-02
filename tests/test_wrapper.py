"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import unittest
from six import PY2
from os import path
from aup import aup_args

@unittest.skipIf(PY2, "Wrapper supports Python3 only.")
class WrapperTestCase(unittest.TestCase):
    file1 = path.join("tests", "data", "wrapper1.json")
    file2 = path.join("tests", "data", "wrapper2.json")

    def testOK(self):
        global var

        var = 0

        @aup_args
        def test1a(x):
            return x
        test1a(self.file1)

        self.assertEqual(var, 1)

        @aup_args
        def test1b(x,a=1):
            return x+a
        test1b(self.file1)

        self.assertEqual(var, 2)

    def test_extra_arg(self):
        @aup_args
        def test2(x,y):
            return x+y
        self.assertRaises(ValueError, test2, self.file1)

    def test_interm_iter(self):
        global var

        var = 0
        @aup_args
        def iteration(x, b):
            global var
            for _ in range(6):
                var += 1

            return var

        iteration(self.file2)
        self.assertEqual(var, 7)

# check that this is called before
# each "aup_args annotated" function call
# because it contains "init" in its name
def test_init(**kwargs):
    global var
    var += 1
