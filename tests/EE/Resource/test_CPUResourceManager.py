"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import unittest
from shutil import copyfile
from shutil import rmtree
import json

from aup import BasicConfig
from aup.EE.Job import Job
from aup.EE.Resource.CPUResourceManager import CPUResourceManager
from aup.utils import get_default_connector

class CPUResourceManagerTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    job = Job("test_Job.py", BasicConfig(), "./tests/EE")
    job_fail = Job("task1.py", BasicConfig(), "./tests/data")
    job_fail2 = Job("task2.py", BasicConfig(), "./tests/data")
    job_fail3 = Job("task3.py", BasicConfig(), "./tests/data")
    job_5 = Job("task5.py", {}, "./tests/data")
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = CPUResourceManager(self.connector, self.n_parallel, eid=1)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_get_resource(self):
        self.assertIsInstance(self.rm.get_available("test", "cpu"), int)
        # !IMPORTANT - currently, there is no user authentication.
        self.assertIsInstance(self.rm.get_available("test2", "cpu"), int)

    def test_run(self):
        def callback(*args):
            self.val = -1

        self.rm.run(self.job, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.executor.shutdown(wait=True)
        self.assertEqual(self.val, -1)

    def test_fail_run(self):
        def callback(*args):
            raise ChildProcessError
        self.rm.run(self.job_fail, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.run(self.job_fail2, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.run(self.job_fail3, self.rm.get_available("test", "cpu"), {}, callback)

    def test_full_run(self):
        def callback(*args):
            pass
        self.rm.run_job(self.job, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.finish_job(self.job.jid, 2.0)
        self.rm.executor.shutdown(wait=True)
        self.assertListEqual([1, 0.1], self.rm.finish())

    def test_finish(self):
        self.rm.suspend()
        self.assertListEqual([1, 0.1], self.rm.finish())

class CPUResourceManagerEarlyStopTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
    job_5.jid = 1
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = CPUResourceManager(self.connector, self.n_parallel,
                                    track_intermediate_results=True,
                                    early_stop={"aup_policy": "median",
                                                "aup_policy_steps": 2},
                                    eid=1)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_early_stop_median(self):
        def callback(*args):
            self.val = -1

        self.rm.policy = "median"
        self.rm.run_job(self.job_5, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)
    
    def test_early_stop_bandit(self):
        def callback(*args):
            self.val = -1

        self.rm.policy = "bandit"
        self.rm.run_job(self.job_5, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)
    
    def test_early_stop_truncation(self):
        def callback(*args):
            self.val = -1

        self.rm.policy = "truncation"
        self.rm.run_job(self.job_5, self.rm.get_available("test", "cpu"), {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

class CPUResourceManagerSaveModelTestCase(unittest.TestCase):
    eid = 2
    n_parallel = 4
    workingdir = os.path.join('tests', 'data')
    auppath = os.path.join("tests", "data", ".aup")
    save_model_folder = os.path.join(workingdir, "aup_models", 'models_{}'.format(eid))
    res_folder = os.path.join(save_model_folder, '15')
    job_1 = Job("task6.py", BasicConfig({"x":5}), "./tests/data")
    job_1.jid = 2
    job_2 = Job("task6.py", BasicConfig({"x":15}), "./tests/data")
    job_2.jid = 3
    job_3 = Job("task6.py", BasicConfig({"x":2}), "./tests/data")
    job_3.jid = 4
    job_4 = Job("task6.py", BasicConfig({"x":1}), "./tests/data")
    job_4.jid = 5
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = CPUResourceManager(self.connector, self.n_parallel,
                                    eid=self.eid,
                                    maximize=True,
                                    save_model=True,
                                    script='task6.py',
                                    workingdir=self.workingdir)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        rmtree(self.save_model_folder)
        os.remove(self.bk_db)

    def test_normal_path(self):
        def callback(*args):
            self.connector.end_job(args[1], args[0], 'FINISHED')
            self.val = -1

        self.val = 0

        self.connector.start_experiment('test', {"name":"test"})

        curr_rid = self.rm.get_available("test", "cpu")
        self.connector.start_job(self.eid, curr_rid, self.job_1.config)
        self.rm.run_job(self.job_1, self.rm.get_available("test", "cpu"), {}, callback)

        curr_rid = self.rm.get_available("test", "cpu")
        self.connector.start_job(self.eid, curr_rid, self.job_2.config)
        self.rm.run_job(self.job_2, self.rm.get_available("test", "cpu"), {}, callback)

        curr_rid = self.rm.get_available("test", "cpu")
        self.connector.start_job(self.eid, curr_rid, self.job_3.config)
        self.rm.run_job(self.job_3, self.rm.get_available("test", "cpu"), {}, callback)

        curr_rid = self.rm.get_available("test", "cpu")
        self.connector.start_job(self.eid, curr_rid, self.job_4.config)
        self.rm.run_job(self.job_4, self.rm.get_available("test", "cpu"), {}, callback)

        self.rm.finish()

        self.assertTrue(os.path.exists(self.res_folder))
        self.assertEqual(self.val, -1)

class CPUResourceManagerMultipleResTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    job_7 = Job("task8.py", BasicConfig({"x":5}), "./tests/data")
    job_7.jid = 2
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0
    mult_res_labels = ["x", "y"]
    eid = 2

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = CPUResourceManager(self.connector, self.n_parallel,
                                    eid=self.eid, multi_res_labels=self.mult_res_labels)

    def tearDown(self):
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_normal_path(self):
        self.val = 0

        def callback(*args):
            self.val = args

        self.connector.start_experiment('test', {"name":"test"})

        curr_rid = self.rm.get_available("test", "cpu")
        self.connector.start_job(self.eid, curr_rid, self.job_7.config)
        self.rm.run_job(self.job_7, self.rm.get_available("test", "cpu"), {}, callback)

        self.rm.finish()

        self.connector.cursor.execute("SELECT * FROM multiple_result WHERE jid=2 order by label_order")
        res = self.connector.cursor.fetchall()

        self.assertEqual(self.val, (6.0, 2))

        self.assertEqual(res[0][1], 1)
        self.assertEqual(res[1][1], 2)
        self.assertEqual(res[0][2], 7)
        self.assertEqual(res[1][2], 8)

if __name__ == '__main__':
    unittest.main()
