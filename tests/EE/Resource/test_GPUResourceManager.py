"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import unittest
from shutil import copyfile
from time import sleep

from aup import BasicConfig
from aup.EE.Job import Job
from aup.EE.Resource.GPUResourceManager import GPUResourceManager
from aup.utils import get_default_connector


class GPUResourceManagerTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    connector = get_default_connector(auppath)
    val = 0
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    job = Job("test_Job.py", BasicConfig(), "./tests/EE")

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = GPUResourceManager(self.connector, self.n_parallel, auppath=self.auppath)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_run(self):
        def callback(*args):
            self.val = -1

        self.rm.run(self.job, self.rm.get_available("test", "gpu"), {}, callback)
        sleep(1.5)  # wait till subprocess finished - handled by rm.finish()

        self.assertEqual(self.val, -1)


if __name__ == "__main__":
    unittest.main()
