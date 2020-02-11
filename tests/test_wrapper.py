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
    
    def testOK(self):
        @aup_args
        def test1a(x):
            return x
        test1a(self.file1)
        
        @aup_args
        def test1b(x,a=1):
            return x+a
        test1b(self.file1)
        
    def test_extra_arg(self):
        @aup_args
        def test2(x,y):
            return x+y
        self.assertRaises(ValueError, test2, self.file1)
        
    