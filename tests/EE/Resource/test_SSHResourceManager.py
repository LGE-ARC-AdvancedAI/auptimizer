"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""

import unittest
import mockssh
import tempfile
import pdb
from time import sleep
from six import PY2

import pkg_resources

from aup.EE.Resource.SSHResourceManager import *
from aup.EE.Job import Job
from aup import BasicConfig
from aup.Proposer import RandomProposer as rp
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

        with mockssh.Server(users) as server1, mockssh.Server(users) as server2:

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

        server1 = mockssh.Server(users).__enter__()

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
                server1 = mockssh.Server(users).__enter__()
                mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey

        mngr.executor.shutdown(wait=True)

        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

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
                    }
                }
        m = rp.RandomProposer(config)

        def callback_fun(score, jid):
            mutex.acquire()
            scores[jid] = score
            mutex.release()

        with mockssh.Server(users) as server1, mockssh.Server(users) as server2:

            mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder,
                    async_run=True, async_reconnect=1, reconn_wait_time=1)
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

        server1 = mockssh.Server(users).__enter__()

        mngr = SSHResourceManager(None, config['n_parallel'], auppath=data_folder,
                                  async_run=True, async_reconnect=5,
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
                server1 = mockssh.Server(users).__enter__()
                mngr.mapping[1] = "mockuser@127.0.0.1:" + str(server1.port) + " " + pkey

        mngr.executor.shutdown(wait=True)

        for key in scores:
            self.assertTrue(scores[key] != "ERROR")

if __name__ == '__main__':
    unittest.main()
