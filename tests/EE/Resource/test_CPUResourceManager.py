import os
import unittest
from shutil import copyfile

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
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = CPUResourceManager(self.connector, self.n_parallel)

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
        self.assertListEqual([1, 0.1], self.rm.finish(1))

    def test_finish(self):
        self.rm.suspend()
        self.assertListEqual([1, 0.1], self.rm.finish(1))


if __name__ == '__main__':
    unittest.main()
