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
import sqlite3
from time import sleep
import json

from .AbstractConnector import AbstractConnector

logger = logging.getLogger(__name__)

DELAY_INTERVAL = 0.1
REPEATED_TIME = 5


def _delayed(func):
    def wrapper(*args, **kwargs):
        flag = 0
        while flag < REPEATED_TIME:
            try:
                results = func(*args, **kwargs)
                return results
            except sqlite3.ProgrammingError:  # pragma: no cover
                logger.critical("update is too frequent, delayed for 1 sec")
                sleep(DELAY_INTERVAL)
                flag += 1
        raise Exception("Failed to query SQLite after %d times" % flag)  # pragma: no cover

    return wrapper


class SQLiteConnector(AbstractConnector):
    def __init__(self, filename):
        super(SQLiteConnector, self).__init__()
        self.connector = sqlite3.connect(filename, check_same_thread=False)
        self.cursor = self.connector.cursor()
        self.cursor.execute("PRAGMA FOREIGN_KEYS = ON;")

    @_delayed
    def _mark_resource(self, rid, status):
        if not isinstance(rid, int):
            raise ValueError("Resource ID is not integer, %s"%type(rid))
        self.cursor.execute("UPDATE resource SET status=? WHERE rid=?", (status, rid))
        self.connector.commit()
        # other utils

    @_delayed
    def close(self):
        self.connector.commit()
        self.connector.close()

    @_delayed
    def end_experiment(self, eid):
        self.cursor.execute("UPDATE experiment SET end_time=strftime('%s','now') WHERE eid=?", (eid,))
        self.connector.commit()

    @_delayed
    def end_job(self, jid, score=None):
        self.cursor.execute("UPDATE job SET end_time=strftime('%s','now'), score=? WHERE jid=?", (score, jid))
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
            self.cursor.execute("SELECT rid FROM resource WHERE status = 'free' AND type = ?;", (rtype,))
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
                FROM job WHERE eid = ? AND score=(select max(score) from job where eid=?)""", (eid, eid))
        else:
            self.cursor.execute("""SELECT jid, score 
                FROM job WHERE eid = ? AND score=(select min(score) from job where eid=?)""", (eid, eid))
        t = self.cursor.fetchone()
        if t is None:
            self.cursor.execute("""select * from experiment where eid=?""", (eid,))
            t = self.cursor.fetchone()
            if t is None:
                raise KeyError("Experiment ID %d not exist" % eid)
            else:
                return []
        return list(t)

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
    def start_experiment(self, username, exp_config_blob):
        self.cursor.execute("SELECT uid FROM user WHERE name = ?", (username,))
        uid = self.cursor.fetchone()
        if uid is None:
            raise ValueError("username %s is not existed" % username)
        uid = uid[0]
        self.cursor.execute("INSERT INTO experiment (uid, exp_config, start_time) VALUES (?,?, strftime('%s','now'))",
                            (uid, exp_config_blob))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def start_job(self, eid, rid, job_config):
        self.cursor.execute("INSERT INTO job (eid, start_time, job_config) VALUES (?, strftime('%s','now'), ?)",
                            (eid, json.dumps(job_config)))
        self.connector.commit()
        jid = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO job_attempt (jid, num, rid, start_time) VALUES (?, 0, ?, (SELECT start_time FROM job j WHERE j.jid=?))",
                            (jid, rid, jid))
        self.connector.commit()
        return jid
    
    @_delayed
    def start_job_attempt(self, rid, jid):
        self.cursor.execute("INSERT INTO job_attempt (jid, num, rid, start_time) VALUES (?, (SELECT num FROM job_attempt jt WHERE jt.jid=? ORDER BY num DESC LIMIT 1)+1, ?, strftime('%s', 'now'))",
                            (jid, jid, rid))
        self.connector.commit()
        return self.cursor.lastrowid

    @_delayed
    def take_available_resource(self, rid):
        self._mark_resource(rid, 'busy')
        return True
