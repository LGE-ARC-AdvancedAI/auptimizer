"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.ET.Connector.SQLiteConnector
================================

If encounter "Failed to query SQLite after xx times" error,
increase DELAY_INTERVAL and REPEATED_TIME to prevent problem temporarily.

APIs
----
"""
import logging
import re
import sqlite3
import threading
from time import sleep
import json
from datetime import datetime

from .AbstractConnector import AbstractConnector

logger = logging.getLogger(__name__)

DELAY_INTERVAL = 0.1
REPEATED_TIME = 5
LOCK = threading.Lock()

def _delayed(func):
    def wrapper(*args, **kwargs):
        flag = 0
        while flag < REPEATED_TIME:
            try:
                LOCK.acquire() # make sure not to call @_delayed functions recursively from one another
                results = func(*args, **kwargs)
                return results
            except sqlite3.ProgrammingError as ex:  # pragma: no cover
                logger.critical("update is too frequent, delayed for 1 sec")
                logger.debug("sqlite3 programming error: {}".format(ex))
                sleep(DELAY_INTERVAL)
                flag += 1
            finally:
                LOCK.release()
        raise Exception("Failed to query SQLite after %d times" % flag)  # pragma: no cover

    return wrapper


class SQLiteConnector(AbstractConnector):
    def __init__(self, filename):
        super(SQLiteConnector, self).__init__()
        self.connector = sqlite3.connect(filename, check_same_thread=False)
        self.cursor = self.connector.cursor()
        self.cursor.execute("PRAGMA FOREIGN_KEYS = ON;")
        self.closed = False

    def _fix_name(self, name):
        if name is None:
            return None

        self.cursor.execute("SELECT JSON_EXTRACT(exp_config, '$.name') as name FROM experiment WHERE name = ?", (name,))
        names = [i[0] for i in self.cursor.fetchall()]
        if not names:
            return name
        self.cursor.execute("SELECT JSON_EXTRACT(exp_config, '$.name') as name FROM experiment WHERE name LIKE ?", ("{} (%)".format(name),))
        last_index = 0
        names = [i[0] for i in self.cursor.fetchall()]
        if names:
            names = [name for name in names if re.findall(r"\(\d+\)$", name)]
            if names:
                indexes = [int(re.findall(r"\(\d+\)$", name)[-1][1:-1]) for name in names]
                last_index = max(indexes)
        return name + " ({})".format(last_index + 1)

    def _mark_resource(self, rid, status):
        if not isinstance(rid, int):
            raise ValueError("Resource ID is not integer, %s"%type(rid))
        self.cursor.execute("UPDATE resource SET status=? WHERE rid=?", (status, rid))
        self.connector.commit()
        # other utils

    @_delayed
    def free_all_resources(self):
        self.cursor.execute("UPDATE resource SET status='free'")
        self.connector.commit()

    @_delayed
    def close(self):
        self.connector.commit()
        self.connector.close()
        self.closed = True

    @_delayed
    def is_closed(self):
        return self.closed

    @_delayed
    def end_experiment(self, eid, status="FINISHED"):
        self.cursor.execute("UPDATE experiment SET end_time=strftime('%s','now'), status=? WHERE eid=?", (status, eid))
        self.connector.commit()

    @_delayed
    def change_experiment_status(self, eid, status="FINISHED"):
        self.cursor.execute("UPDATE experiment SET status=? WHERE eid=?", (status, eid))
        self.connector.commit()

    @_delayed
    def end_job(self, jid, score=None, status=None):
        self.cursor.execute("UPDATE job SET end_time=strftime('%s','now'), status=?, score=? WHERE jid=?", (status, score, jid))
        self.connector.commit()

    @_delayed
    def end_job_attempt(self, jid):
        self.cursor.execute("""UPDATE job_attempt SET end_time=strftime('%s', 'now') WHERE jaid=(
                                    SELECT jaid FROM job_attempt jt WHERE jt.jid=? ORDER BY num DESC LIMIT 1)""", (jid,))
        self.connector.commit()

    @_delayed
    def free_used_resource(self, rid):
        self._mark_resource(rid, 'free')
        return True

    @_delayed
    def get_all_experiment(self, username=None):
        if username:
            self.cursor.execute("SELECT uid FROM user WHERE name = ?", (username,))
            uid = self.cursor.fetchone()
            if uid is None:
                raise ValueError("User %s does not exist" % username)
            self.cursor.execute("SELECT eid FROM experiment WHERE uid = ?", (uid[0],))
        else:
            self.cursor.execute("SELECT eid FROM experiment")
        eids = self.cursor.fetchall()
        return [e[0] for e in eids]  # unzip tuple of one element

    @_delayed
    def get_available_resource(self, username, rtype, rid_blacklist=None):
        rids = []
        if rid_blacklist:
            # Initial approach:
            # self.cursor.execute("SELECT rid FROM resource WHERE status = 'free' AND type = ? AND rid NOT IN ?;", (rtype, rid_blacklist))
            # However, this does not work with sqlite3, so the following approach was ultimately selected
            self.cursor.execute("SELECT rid FROM resource WHERE status = 'free' AND type = ? AND rid NOT IN ({});".format(
                                    ",".join("?" * len(rid_blacklist))), (rtype,) + tuple(rid_blacklist))
            rids = [i[0] for i in self.cursor.fetchall()]
        if not rids:
            # An attempt was made to filter out resources, but this was not possible (the only
            # available resource are the ones blacklisted)
            self.cursor.execute("SELECT rid FROM resource WHERE status = 'free' AND instr(?, type) != 0;", (rtype,))
            rids = [i[0] for i in self.cursor.fetchall()]
        return rids

    @_delayed
    def get_all_history(self, eid):
        self.cursor.execute("SELECT * FROM job WHERE eid = ?", (eid,))
        return self.cursor.fetchall()

    @_delayed
    def get_best_result(self, eid, maximize=True):
        if maximize:
            self.cursor.execute("""SELECT jid, score 
                FROM job WHERE eid = ? AND score=(select max(score) from job where eid=? AND typeof(score) = 'real')""", (eid, eid))
        else:
            self.cursor.execute("""SELECT jid, score 
                FROM job WHERE eid = ? AND score=(select min(score) from job where eid=? AND typeof(score) = 'real')""", (eid, eid))
        t = self.cursor.fetchone()
        if t is None:
            self.cursor.execute("""select * from experiment where eid=?""", (eid,))
            t = self.cursor.fetchone()
            if t is None:
                raise KeyError("Experiment ID %d not exist" % eid)
            else:
                return None
        return list(t)

    @_delayed
    def get_best_result_config(self, eid, maximize=True):
        if maximize:
            self.cursor.execute("""SELECT job_config 
                FROM job WHERE eid = ? AND score=(select max(score) from job where eid=? AND typeof(score) = 'real')""", (eid, eid))
        else:
            self.cursor.execute("""SELECT job_config 
                FROM job WHERE eid = ? AND score=(select min(score) from job where eid=? AND typeof(score) = 'real')""", (eid, eid))
        t = self.cursor.fetchone()

        return t

    @_delayed
    def get_running_job(self, eid):
        self.cursor.execute("SELECT jid FROM job WHERE eid = ?", (eid,))
        jid = [i[0] for i in self.cursor.fetchall()]
        logger.debug("%s" % jid)
        return jid

    @_delayed
    def get_resource_type(self):
        self.cursor.execute("SELECT DISTINCT type from resource;")
        return [i[0] for i in self.cursor.fetchall()]

    @_delayed
    def start_experiment(self, username, exp_config):
        self.cursor.execute("SELECT uid FROM user WHERE name = ?", (username,))
        uid = self.cursor.fetchone()
        if uid is None:
            raise ValueError("username %s is not existed" % username)
        uid = uid[0]
        exp_config['name'] = self._fix_name(exp_config.get('name', None))
        self.cursor.execute("INSERT INTO experiment (uid, exp_config, start_time, error_msg, status) \
                                VALUES (?,?, strftime('%s','now'), NULL, 'RUNNING')",
                            (uid, json.dumps(exp_config)))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def start_experiment_by_eid(self, eid):
        self.cursor.execute("DELETE FROM multiple_result WHERE eid={eid}".format(eid=eid))
        self.connector.commit()
        self.cursor.execute("DELETE FROM job_attempt WHERE jid in (SELECT jid FROM job WHERE eid={eid})".format(eid=eid))
        self.connector.commit()
        self.cursor.execute("DELETE FROM intermediate_result WHERE jid in (SELECT jid FROM job WHERE eid={eid})".format(eid=eid))
        self.connector.commit()
        self.cursor.execute("DELETE FROM job WHERE eid={eid}".format(eid=eid))
        self.connector.commit()
        self.cursor.execute("UPDATE experiment SET start_time = strftime('%s','now'), end_time = NULL, \
                            error_msg = NULL, status = 'RUNNING' WHERE eid={eid}".format(eid=eid))
        self.connector.commit()

    @_delayed
    def start_job(self, eid, rid, job_config):
        self.cursor.execute("INSERT INTO job (eid, start_time, job_config, status) VALUES (?, strftime('%s','now'), ?, 'RUNNING')",
                            (eid, json.dumps(job_config)))
        self.connector.commit()
        jid = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO job_attempt (jid, num, rid, start_time) VALUES (?, 0, ?, (SELECT start_time FROM job j WHERE j.jid=?))",
                            (jid, rid, jid))
        self.connector.commit()
        return jid
    
    @_delayed
    def start_job_attempt(self, rid, jid):
        self.cursor.execute("INSERT INTO job_attempt (jid, num, rid, start_time) \
                            VALUES (?, (SELECT num FROM job_attempt jt WHERE jt.jid=? ORDER BY num DESC LIMIT 1)+1, ?, strftime('%s', 'now'))",
                            (jid, jid, rid))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def update_job_status(self, jid, status):
        self.cursor.execute("UPDATE job SET status=? WHERE jid=?", (status, jid))
        self.connector.commit()

    @_delayed
    def take_available_resource(self, rid):
        self._mark_resource(rid, 'busy')
        return True

    @_delayed
    def save_intermediate_result(self, jid, score):
        self.cursor.execute("""
            INSERT INTO intermediate_result (num, jid, score, receive_time) 
            VALUES ((SELECT CASE EXISTS(SELECT num FROM intermediate_result ir WHERE ir.jid=?) 
                        WHEN 0 THEN -1 
                        WHEN 1 THEN (SELECT num FROM intermediate_result ir WHERE ir.jid=? ORDER BY num DESC LIMIT 1) END) + 1,
                    ?, ?, strftime('%s', 'now'))""",
            (jid, jid, jid, score))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def get_intermediate_results_job(self, jid):
        self.cursor.execute("""
            SELECT score
            FROM intermediate_result ir
            WHERE ir.jid=?
            ORDER BY ir.num ASC;""", (jid,))
        rows = [row[0] for row in self.cursor.fetchall()]
        return rows

    @_delayed
    def get_intermediate_results_jobs(self, jids):
        self.cursor.execute("""
            SELECT jid, score
            FROM intermediate_result ir
            WHERE ir.jid in ({})
            ORDER BY ir.jid, ir.num ASC;""".format(",".join("?" * len(jids))), tuple(jids))
        rows = self.cursor.fetchall()
        results = {}
        for jid, score in rows:
            if jid not in results:
                results[jid] = []
            results[jid] += [score]
        return results

    @_delayed
    def get_intermediate_results_experiment(self, eid, status):
        self.cursor.execute("""
            SELECT jid, score
            FROM intermediate_result ir
            WHERE EXISTS(SELECT 1 FROM job j WHERE j.jid=ir.jid AND j.eid=? AND j.status=?)
            ORDER BY ir.jid, ir.num ASC;""", (eid, status))
        rows = self.cursor.fetchall()
        results = {}
        for jid, score in rows:
            if jid not in results:
                results[jid] = []
            results[jid] += [score]
        return results

    @_delayed
    def create_experiment(self, username, exp_config):
        self.cursor.execute("SELECT uid FROM user WHERE name = ?", (username,))
        uid = self.cursor.fetchone()
        if uid is None:
            raise ValueError("username %s is not existed" % username)
        uid = uid[0]
        exp_config['name'] = self._fix_name(exp_config.get('name', None))
        self.cursor.execute("INSERT INTO experiment (uid, exp_config, start_time, end_time, error_msg, status) \
                            VALUES (?,?, NULL, NULL, NULL, 'CREATED')",
                            (uid, json.dumps(exp_config)))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def delete_experiment(self, eid):
        self.cursor.execute("SELECT eid FROM experiment WHERE eid = ?", (eid,))
        check_eid = self.cursor.fetchone()
        if check_eid is None:
            return False

        self.cursor.execute("DELETE FROM multiple_result WHERE eid={eid};".format(eid=eid))
        self.cursor.execute("DELETE FROM job_attempt WHERE jid in (SELECT jid FROM job WHERE eid={eid})".format(eid=eid))
        self.cursor.execute("DELETE FROM intermediate_result WHERE jid in (SELECT jid FROM job WHERE eid={eid})".format(eid=eid))
        self.cursor.execute("DELETE FROM job WHERE eid={eid}".format(eid=eid))
        self.cursor.execute("DELETE from experiment WHERE eid={eid}".format(eid=eid))
        self.connector.commit()

        return True

    @_delayed
    def get_experiment_status(self, eid):
        self.cursor.execute("SELECT status FROM experiment WHERE eid = ? LIMIT 1", (eid,))
        status = self.cursor.fetchone()
        
        if status is None:
            raise ValueError("Requested experiment for get_experiment_status not found in database!")
        
        return status[0]
    
    @_delayed
    def maybe_get_experiment_status(self, eid):
        # TODO: we need a way to recursively call these functions without locking issues (due to @_delayed)
        if self.closed:
            return None

        self.cursor.execute("SELECT status FROM experiment WHERE eid = ? LIMIT 1", (eid,))
        status = self.cursor.fetchone()

        if status is None:
            raise ValueError("Requested experiment for get_experiment_status not found in database!")

        return status[0]

    @_delayed
    def log_error_message(self, eid, msg):
        self.cursor.execute("UPDATE experiment SET error_msg=? WHERE eid=? and error_msg is NULL", (msg, eid))
        self.connector.commit()

    @_delayed
    def save_multiple_results(self, jid, irid, eid, labels, scores):
        receive_time = int(datetime.now().timestamp())

        self.cursor.execute("""
                    SELECT count(*) FROM sqlite_master WHERE type='table' AND name='multiple_result'""")
        res = self.cursor.fetchone()[0]

        if res == 0:
            logger.warning("multiple_result table not found, continuing without saving multiple results! \n \
                            Please consider updating Auptimizer to >=1.5")
            return

        for idx in range(len(scores)):
            self.cursor.execute("""
                    INSERT INTO multiple_result (label_order, value, receive_time, jid, irid, eid, is_last_result)
                    VALUES (?, ?, ?, ?, ?, ?, 0)""",
                    (idx+1, scores[idx], receive_time, jid, irid, eid))

        self.connector.commit()

    @_delayed
    def set_last_multiple_results(self, eid, jid, num_labels):
        self.cursor.execute("""
                    SELECT mrid FROM multiple_result WHERE eid=? AND jid=?
                    ORDER BY mrid DESC LIMIT 0,?""", (eid, jid, num_labels))
        res = self.cursor.fetchall()

        for mrid in res:
            self.cursor.execute("""
                            UPDATE multiple_result SET is_last_result=1 WHERE mrid=?""", (mrid[0],))

        self.connector.commit()

