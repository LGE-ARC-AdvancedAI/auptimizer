"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import os
import sqlite3
import unittest
from six.moves import configparser

from aup.ET.Connector.SQLiteConnector import SQLiteConnector
from aup.setupdb import sqlite


class SQLiteConnectorTestCase(unittest.TestCase):
    db_file = os.path.join("tests", "data", "sqlite3.db")
    config = configparser.ConfigParser()
    config.add_section("Auptimizer")
    config.set("Auptimizer", "SQLITE_FILE", db_file)
    config.set("Auptimizer", "gpu_mapping", """{"1": 0, "2": 1}""")
    username = "test"
    name = "unittest"

    def setUp(self):
        sqlite.create_database(self.config, [self.name], 1, self.username)

    def tearDown(self):
        os.remove(self.db_file)

    def test_resource(self):
        """Test resource allocation"""
        connector = SQLiteConnector(self.db_file)
        self.assertListEqual(connector.get_resource_type(), [u'gpu', u'cpu', u'passive'])

        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual({1, 2}, set(rids))

        connector.take_available_resource(1)
        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual({2}, set(rids))

        connector.free_used_resource(1)
        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual({1, 2}, set(rids))

        connector.take_available_resource(2)
        connector.take_available_resource(1)
        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual(set([]), set(rids))

        connector.free_used_resource(1)
        connector.free_used_resource(2)
        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual({1, 2}, set(rids))
        connector.close()

    def test_experiment(self):
        """test experiment start and stop"""
        connector = SQLiteConnector(self.db_file)
        eid1 = connector.start_experiment(self.name, {'name':'exp1'})
        eid2 = connector.start_experiment(self.name, {'name':'exp2'})
        connector.end_experiment(eid1)
        connector.end_experiment(eid2)

        eids = connector.get_all_experiment(username=self.name)
        self.assertListEqual(eids, [1, 2])

        eids = connector.get_all_experiment()
        self.assertListEqual(eids, [1, 2])

        self.assertRaises(ValueError, connector.get_all_experiment, "not-exist")

    def test_job(self):
        """test job start and stop"""
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'exp1'})
        rid = 1
        jid1 = connector.job_started(eid, rid, "job1")
        jid2 = connector.job_started(eid, rid, "job1")

        self.assertListEqual(connector.get_running_job(eid), [jid1, jid2])

        connector.job_finished(eid, jid2, -100.)
        connector.job_finished(eid, jid1, 100.)

        self.assertRaises(sqlite3.IntegrityError, connector.job_started,1, 20, "job2")
        self.assertListEqual(connector.get_best_result(1, maximize=True), [jid1, 100.])
        self.assertListEqual(connector.get_best_result(1, maximize=False), [jid2, -100.])
        connector.close()

    def test_reset(self):
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'exp1'})
        rids = connector.get_available_resource(self.username, 'gpu')
        self.assertEqual({1, 2}, set(rids))
        jid = connector.job_started(eid, 1, "job1")
        connector.get_available_resource(self.username, "gpu")
        sqlite.reset(self.config)
        self.assertEqual({1, 2}, set(rids))
        r_jid = connector.get_all_history(1)[0][0]
        self.assertEqual(r_jid, jid)

    def test_job_attempt(self):
        """ Tests SQLiteConnector.start_job_attempt and SQLiteConnector.end_job_attempt"""
        rid = 1
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'test'})
        jid = connector.job_started(eid, rid, "job1")
        connector.end_job_attempt(jid)

        connector.cursor.execute("SELECT jaid, jid, num, rid, start_time, end_time FROM job_attempt;")
        res = connector.cursor.fetchall()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1], 1)
        self.assertEqual(res[0][2], 0)
        self.assertEqual(res[0][3], rid)
        self.assertNotEqual(res[0][-1], None)

        connector.cursor.execute("SELECT jid, end_time FROM job;")
        res = connector.cursor.fetchall()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][-1], None)

        connector.job_finished(eid, jid, -100.)
        connector.close()

    def test_get_available_resource(self):
        """Tests SQLiteConnector.get_available_resource"""
        rid = 1
        connector = SQLiteConnector(self.db_file)
        rids = connector.get_available_resource("test", "cpu")
        self.assertGreaterEqual(len(rids), 1)
        rids1 = connector.get_available_resource("test", "cpu", rids[:-1])
        self.assertEqual(len(rids1), 1)
        rids2 = connector.get_available_resource("test", "cpu", rids)
        self.assertEqual(len(rids), 1)

        def test_save_intermediate_result(self):
            """Test saving of intermediate results"""
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'test'})
        rid = 1
        jid1 = connector.job_started(eid, rid, "job1")

        self.assertListEqual(connector.get_running_job(eid), [jid1])

        connector.save_intermediate_result(jid1, -50.0)
        connector.save_intermediate_result(jid1, -75.0)
        connector.save_intermediate_result(jid1, -100.0)
        connector.job_finished(eid, jid1, -100.)

        connector.cursor.execute("SELECT num, score FROM intermediate_result WHERE jid=? ORDER BY num ASC;", (jid1,))
        irs = connector.cursor.fetchall()
        self.assertEqual(len(irs), 3)
        self.assertEqual(irs[0][0], 0)
        self.assertEqual(irs[1][0], 1)
        self.assertEqual(irs[2][0], 2)
        self.assertEqual(irs[0][1], -50.0)
        self.assertEqual(irs[1][1], -75.0)
        self.assertEqual(irs[2][1], -100.0)
        connector.close()

    def test_get_intermediate_results_job(self):
        """Test for getting intermediate results for a given job"""
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'exp1'})
        rid = 1
        jid1 = connector.job_started(eid, rid, "job1")

        self.assertListEqual(connector.get_running_job(eid), [jid1])

        connector.save_intermediate_result(jid1, -50.0)
        connector.save_intermediate_result(jid1, -75.0)
        connector.save_intermediate_result(jid1, -100.0)
        connector.job_finished(eid, jid1, -100.)
        
        ir = connector.get_intermediate_results_job(jid1)
        self.assertEqual(len(ir), 3)
        self.assertEqual(ir[0], -50.)
        self.assertEqual(ir[1], -75.)
        self.assertEqual(ir[2], -100.)

    def test_get_intermediate_results_jobs(self):        
        """Test for getting intermediate results for some given jobs"""
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'exp1'})
        jid1 = connector.job_started(eid, 1, "job1")
        jid2 = connector.job_started(eid, 2, "job2")

        self.assertListEqual(connector.get_running_job(eid), [jid1, jid2])

        connector.save_intermediate_result(jid1, -50.0)
        connector.save_intermediate_result(jid1, -75.0)
        connector.save_intermediate_result(jid1, -100.0)
        connector.job_finished(eid, jid1, -100.)
        
        connector.save_intermediate_result(jid2, 50.0)
        connector.save_intermediate_result(jid2, 75.0)
        connector.save_intermediate_result(jid2, 100.0)
        connector.job_finished(eid, jid2, 100.)
        
        ir = connector.get_intermediate_results_jobs([jid1, jid2])
        self.assertEqual(len(ir), 2)
        self.assertEqual(len(ir[jid1]), 3)
        self.assertEqual(ir[jid1][0], -50.)
        self.assertEqual(ir[jid1][1], -75.)
        self.assertEqual(ir[jid1][2], -100.)
        self.assertEqual(len(ir[jid2]), 3)
        self.assertEqual(ir[jid2][0], 50.)
        self.assertEqual(ir[jid2][1], 75.)
        self.assertEqual(ir[jid2][2], 100.)

    def test_get_intermediate_results_experiment(self):
        """Test for getting intermediate results for a given experiment"""
        connector = SQLiteConnector(self.db_file)
        eid = connector.start_experiment(self.name, {'name':'exp1'})
        jid1 = connector.job_started(eid, 1, "job1")
        jid2 = connector.job_started(eid, 2, "job2")

        self.assertListEqual(connector.get_running_job(eid), [jid1, jid2])

        connector.save_intermediate_result(jid1, -50.0)
        connector.save_intermediate_result(jid1, -75.0)
        connector.job_finished(eid, jid1, -75, status="EARLY_STOPPED")
        
        connector.save_intermediate_result(jid2, 50.0)
        connector.save_intermediate_result(jid2, 75.0)
        connector.save_intermediate_result(jid2, 100.0)
        connector.job_finished(eid, jid2, 100., status="FINISHED")
        
        ir = connector.get_intermediate_results_experiment(eid, status="FINISHED")
        self.assertEqual(len(ir), 1)
        self.assertEqual(ir.get(jid1, None), None)
        self.assertNotEqual(ir.get(jid2, None), None)
        self.assertEqual(len(ir[jid2]), 3)
        self.assertEqual(ir[jid2][0], 50.)
        self.assertEqual(ir[jid2][1], 75.)
        self.assertEqual(ir[jid2][2], 100.)

if __name__ == '__main__':
    unittest.main()
