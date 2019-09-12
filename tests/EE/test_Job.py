#!/usr/bin/env python
from unittest import TestCase

import logging
import os
import shutil

from aup.EE.Job import Job

logging.disable(logging.FATAL)


class JobTestCase(TestCase):
    def setUp(self):
        self.path = os.path.join("tests", "EE")
        shutil.rmtree(os.path.join(self.path, "jobs"), ignore_errors=True)

    def test_verify_folder(self):
        job = Job("test_Job.py", {}, self.path)
        self.assertTrue(job.verify_local())  # working demo

        job = Job("missing_script", {}, self.path)
        self.assertRaises(EnvironmentError, job.verify_local)  # missing script

        job = Job("__init__.py", {}, self.path)
        self.assertRaises(EnvironmentError, job.verify_local)  # not executable

        job = Job("test_Job.py", {}, os.path.join("tests", "data", "wrong"))
        self.assertRaises(EnvironmentError, job.verify_local)


if __name__ == "__main__":
    from aup.utils import print_result
    print_result("10.")
