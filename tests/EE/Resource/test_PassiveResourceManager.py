"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import unittest
from shutil import copyfile

from aup import BasicConfig
from aup.EE.Job import Job
from aup.EE.Resource.PassiveResourceManager import PassiveResourceManager
from aup.utils import get_default_connector


class PassiveRMTestCase(unittest.TestCase):
    auppath = os.path.join("tests", "data", ".aup")
    job = Job("task1.py", BasicConfig(), "./tests/EE")
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = PassiveResourceManager(self.connector)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_get_available(self):
        self.assertEqual(10, self.rm.get_available("test", "passive"))
        self.connector.take_available_resource(10)
        self.assertEqual(None, self.rm.get_available("test", "passive"))
        self.rm.running = True
        self.assertEqual(None, self.rm.get_available("test", "passive"))


if __name__ == '__main__':
    unittest.main()
