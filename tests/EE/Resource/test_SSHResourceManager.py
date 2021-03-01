"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""

import unittest
import mockssh
import tempfile
import pdb
from shutil import copyfile
from time import sleep
from six import PY2

import pkg_resources

from aup.EE.Resource.SSHResourceManager import *
from aup.EE.Job import Job
from aup import BasicConfig
from aup.Proposer import RandomProposer as rp
from aup.utils import get_default_connector
from threading import Lock

@unittest.skipIf(PY2, "mockssh and paramiko do not support python 2.7")
class SSHResourceManagerTestCase(unittest.TestCase):

    def test_parse_hostname(self):
        self.assertRaises(ValueError, parse_hostname, "testip")
        self.assertRaises(Exception, parse_hostname, "a@b:cc")

        self.assertRaises(IOError, parse_hostname, "a@b non-file")
        self.assertTupleEqual(('a', 'b', 22, None), parse_hostname("a@b"))

    def test_ssh_session(self):
        pkey = pkg_resources.resource_filename("mockssh", 'server-key')
        data_folder = pkg_resources.resource_filename(__name__, 'data')
        users = {
            "mockuser": pkey,
        }
        scores = {}
        mutex = Lock()

        config = {  'workingdir': data_folder,
                    'n_parallel': 2,
                    'resource': 'node',
                    'proposer': 'random',
                    'script': os.path.join(data_folder,"script","rosenbrock_hpo.py"),
                    'n_samples': 10,
                    'random_seed': 10,
                    'parameter_config': [{'name': 'x', 'type': 'float', 'range': [-5, 5]},
                                        {'name': 'y', 'type': 'float', 'range': [-5, 5]}],
                    "runtime_args": {
                        "prescript": "export CUDA_VISIBLE_DEVICES=-1",
                        "postscript": "echo $CUDA_VISIBLE_DEVICES",
                        "overwrite": 'true'
                    }
                }
        m = rp.RandomProposer(config)

        def callback_fun(score, jid):
            mutex.acquire()
            scores[jid] = score
            mutex.release()

        server1 = mockssh.Server(users)
        server1.__enter__()

        server2 = mockssh.Server(users)
        server2.__enter__()

        mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder,
                                    reconn_wait_time=3, max_retries=3)
        mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey
        mngr.mapping[2] = "mockuser@127.0.0.1:" + str(server2.port) + " " + pkey

        for i in range(0, config['n_samples'], 2):
            proposal = m.get()
            job1 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
            job1.jid = i
            mngr.run(job1, 1, None, callback_fun, overwrite=True)

            proposal = m.get()
            job2 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
            job2.jid = i+1
            mngr.run(job2, 2, None, callback_fun, overwrite=True)

        mngr.executor.shutdown(wait=True)

        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

    def test_recover_ssh_session(self):
        pkey = pkg_resources.resource_filename("mockssh", 'server-key')
        data_folder = pkg_resources.resource_filename(__name__, 'data')
        users = {
            "mockuser": pkey,
        }
        scores = {}
        mutex = Lock()

        config = {  'workingdir': data_folder,
                    'n_parallel': 1,
                    'resource': 'node',
                    'proposer': 'random',
                    'script': os.path.join(data_folder,"script","rosenbrock_hpo.py"),
                    'n_samples': 10,
                    'random_seed': 10,
                    'parameter_config': [{'name': 'x', 'type': 'float', 'range': [-5, 5]},
                                        {'name': 'y', 'type': 'float', 'range': [-5, 5]}],
                    "runtime_args": {
                        "prescript": "export CUDA_VISIBLE_DEVICES=-1",
                        "postscript": "echo $CUDA_VISIBLE_DEVICES",
                        "overwrite": 'true'
                    }
                }
        m = rp.RandomProposer(config)

        def callback_fun(score, jid):
            mutex.acquire()
            scores[jid] = score
            mutex.release()

        server1 = mockssh.Server(users)
        server1.__enter__()

        mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder,
                                        reconn_wait_time=5, max_retries=5)
        mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey

        for i in range(config['n_samples']):
            proposal = m.get()
            job1 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
            job1.jid = i
            mngr.run(job1, 1, None, callback_fun, overwrite=True)

            if i == int(config['n_samples'] / 2):
                # drop server and check after reopen it if we recover
                server1.__exit__()
                del server1
                sleep(7)
                server1 = mockssh.Server(users)
                server1.__enter__()
                mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey
        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

class SSHResourceManagerEarlyStopTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    workingdir = os.path.join("tests", "data")
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0
    pkey = pkg_resources.resource_filename("mockssh", 'server-key')
    users = {"mockuser": pkey}

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = SSHResourceManager(self.connector, self.n_parallel, 
                                     track_intermediate_results=True,
                                     early_stop={"aup_policy": "median",
                                                "aup_policy_steps": 2},
                                     eid=1, auppath=self.auppath)
        self.server = mockssh.Server(self.users).__enter__()
        self.rm.mapping[1] = "mockuser@127.0.0.1:" + str(self.server.port) + " " + self.pkey
        self.val = 0

    def tearDown(self):
        self.server.__exit__()
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_early_stop_median(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "median"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

        self.rm.executor.shutdown(wait=True)

    def test_early_stop_bandit(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "bandit"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

    def test_early_stop_truncation(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "truncation"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

class AsyncSSHResourceManagerTestCase(unittest.TestCase):
    def test_parse_hostname(self):
        self.assertRaises(ValueError, parse_hostname, "testip")
        self.assertRaises(Exception, parse_hostname, "a@b:cc")

        self.assertRaises(IOError, parse_hostname, "a@b non-file")
        self.assertTupleEqual(('a', 'b', 22, None), parse_hostname("a@b"))

    def test_async_ssh_session(self):
        pkey = pkg_resources.resource_filename("mockssh", 'server-key')
        data_folder = pkg_resources.resource_filename(__name__, 'data')
        users = {
            "mockuser": pkey,
        }
        scores = {}
        mutex = Lock()

        config = {  'workingdir': data_folder,
                    'n_parallel': 2,
                    'resource': 'node',
                    'proposer': 'random',
                    'script': os.path.join(data_folder,"script","rosenbrock_hpo.py"),
                    'n_samples': 10,
                    'random_seed': 10,
                    'parameter_config': [{'name': 'x', 'type': 'float', 'range': [-5, 5]},
                                        {'name': 'y', 'type': 'float', 'range': [-5, 5]}],
                    "runtime_args": {
                        "prescript": "export CUDA_VISIBLE_DEVICES=-1",
                        "postscript": "echo $CUDA_VISIBLE_DEVICES",
                        "overwrite": 'true'
                    },
                    "resource_args": {
                        "async_run": 'true',
                        "async_reconnect": 1
                    }
                }
        m = rp.RandomProposer(config)

        def callback_fun(score, jid):
            mutex.acquire()
            scores[jid] = score
            mutex.release()

        with mockssh.Server(users) as server1, mockssh.Server(users) as server2:

            mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder, async_reconnect=1, async_run=True)
            mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey
            mngr.mapping[2] = "mockuser@127.0.0.1:" + str(server2.port) + " " + pkey

            for i in range(0, config['n_samples'], 2):
                proposal = m.get()
                job1 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
                job1.jid = i
                mngr.run(job1, 1, None, callback_fun, overwrite=True)

                proposal = m.get()
                job2 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
                job2.jid = i+1
                mngr.run(job2, 2, None, callback_fun, overwrite=True)

            mngr.executor.shutdown(wait=True)

        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

    def test_async_recover_ssh_session(self):
        pkey = pkg_resources.resource_filename("mockssh", 'server-key')
        data_folder = pkg_resources.resource_filename(__name__, 'data')
        users = {
            "mockuser": pkey,
        }
        scores = {}
        mutex = Lock()

        config = {  'workingdir': data_folder,
                    'n_parallel': 1,
                    'resource': 'node',
                    'proposer': 'random',
                    'script': os.path.join(data_folder,"script","rosenbrock_hpo.py"),
                    'n_samples': 4,
                    'random_seed': 10,
                    'parameter_config': [{'name': 'x', 'type': 'float', 'range': [-5, 5]},
                                        {'name': 'y', 'type': 'float', 'range': [-5, 5]}],
                    "runtime_args": {
                        "prescript": "export CUDA_VISIBLE_DEVICES=-1",
                        "postscript": "echo $CUDA_VISIBLE_DEVICES",
                        "overwrite": 'true'
                    },
                    "resource_args": {
                        "async_run": 'true',
                        "async_reconnect": 1
                    }
                }
        m = rp.RandomProposer(config)

        def callback_fun(score, jid):
            mutex.acquire()
            scores[jid] = score
            mutex.release()

        server1 = mockssh.Server(users).__enter__()

        mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder,
                                  async_reconnect=1,
                                  reconn_wait_time=1, max_retries=5, async_run=True)
        mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey

        for i in range(config['n_samples']):
            proposal = m.get()
            job1 = Job(config['script'], BasicConfig(**proposal), config['workingdir'])
            job1.jid = i
            mngr.run(job1, 1, None, callback_fun, overwrite=True)

            if i == int(config['n_samples'] / 2):
                # drop server and check after reopen it if we recover
                server1.__exit__()
                del server1
                sleep(2)
                server1 = mockssh.Server(users).__enter__()
                mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey

        mngr.executor.shutdown(wait=True)

        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

class AsyncSSHResourceManagerEarlyStopTestCase(unittest.TestCase):
    n_parallel = 1
    auppath = os.path.join("tests", "data", ".aup")
    workingdir = os.path.join("tests", "data")
    ori_db = os.path.join(auppath, "sqlite3.db")
    bk_db = os.path.join(auppath, "bk.db")
    val = 0
    pkey = pkg_resources.resource_filename("mockssh", 'server-key')
    users = {"mockuser": pkey}

    def setUp(self):
        copyfile(self.ori_db, self.bk_db)
        self.connector = get_default_connector(self.auppath)
        self.rm = SSHResourceManager(self.connector, self.n_parallel, 
                                     track_intermediate_results=True,
                                     early_stop={"aup_policy": "median",
                                                "aup_policy_steps": 2},
                                     eid=1, async_reconnect=1, reconn_wait_time=1,
                                     auppath=self.auppath,
                                     async_run=True)
        self.server = mockssh.Server(self.users).__enter__()
        self.rm.mapping[1] = "mockuser@127.0.0.1:" + str(self.server.port) + " " + self.pkey
        self.val = 0

    def tearDown(self):
        self.server.__exit__()
        copyfile(self.bk_db, self.ori_db)
        os.remove(self.bk_db)

    def test_early_stop_median(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "median"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

    def test_early_stop_bandit(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "bandit"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

    def test_early_stop_truncation(self):
        mutex = Lock()
        def callback(*args):
            mutex.acquire()
            self.val = -1
            mutex.release()

        self.rm.policy = "truncation"
        job_5 = Job("task5.py", BasicConfig({"x":5}), "./tests/data")
        job_5.jid = 1
        self.rm.run_job(job_5, 1, {}, callback)
        self.rm.finish()

        self.assertDictEqual(self.rm.interm_job_res, {1: [6.0, 7.0, 8.0, 9.0, 10.0, 11.0]})
        self.assertEqual(self.val, -1)

if __name__ == '__main__':
    unittest.main()
