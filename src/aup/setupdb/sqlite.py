#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Set up SQLite database for Auptimizer
=====================================

This code is running automatically during the setup.
If needed, it can be used as

.. program-output:: python3 -m aup.setupdb.sqlite -h

APIs
----
"""
import sqlite3
import os
import click
import json
import logging
import coloredlogs
from ..utils import get_default_username, LOG_LEVEL

from six.moves.configparser import ConfigParser

logger = logging.getLogger("aup.setupdb.sqlite")


def _create_connection(db_file):
    filename = os.path.expanduser(db_file)
    return sqlite3.connect(filename)


def _insert_resource(config, res_name, cursor, name, type):
    if not config.has_option("Auptimizer", res_name):
        return
    for i in json.loads(config.get("Auptimizer", res_name)):
        cursor.execute("INSERT INTO resource (rid, name, type, status) VALUES (?,?,?,?)",
                       (i, name, type, "free"))


def create_database(config, usernames, cpu, name):
    """Create new database for Auptimizer
    
    :param config: contains ``SQLITE_FILE``, ``gpu_mapping`` under ``Auptimizer`` section
    :type config: configparser.ConfigParser
    :param usernames: list of username, not used
    :type usernames: list(str)
    :param cpu: number of CPUs for parallel jobs
    :type cpu: int
    :param name: node information, not used
    :type name: str
    """
    try:
        file = config.get("Auptimizer", "SQLITE_FILE")
    except Exception as e:
        logger.fatal("failed to retrieve SQLITE_FILE from aup environment")
        raise e
    conn = _create_connection(file)
    c = conn.cursor()

    # User Table
    c.execute("DROP TABLE IF EXISTS user;")
    c.execute("""CREATE TABLE user
        (uid INTEGER PRIMARY KEY NOT NULL, name TEXT UNIQUE, permission BLOB);""")

    # Resource Table
    c.execute("DROP TABLE IF EXISTS resource;")
    c.execute("""CREATE TABLE resource
        (rid INTEGER PRIMARY KEY NOT NULL, name TEXT, type TEXT, status TEXT)""")

    # Experiment Table
    c.execute("DROP TABLE IF EXISTS experiment;")
    c.execute("""CREATE TABLE experiment 
        (eid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, uid INTEGER, start_time INTEGER, end_time INTEGER,
         status TEXT CHECK(status IN ('CREATED', 'RUNNING', 'STOPPED', 'FINISHED', 'FAILED', 'STOPPING', 'REQUEST_STOP')),
         exp_config BLOB, error_msg TEXT NULL,
        FOREIGN KEY(uid) REFERENCES user(uid));""")

    # Job Table
    c.execute("DROP TABLE IF EXISTS job;")
    c.execute("""CREATE TABLE job
        (jid INTEGER PRIMARY KEY NOT NULL, score REAL, eid INTEGER, start_time INTEGER, end_time INTEGER,
        status TEXT CHECK(status IN ('RUNNING', 'EARLY_STOPPED', 'FINISHED', 'FAILED')),
        job_config BLOB,
        FOREIGN KEY(eid) REFERENCES experiment(eid));""")

    # Job Attempt Table
    c.execute("DROP TABLE IF EXISTS job_attempt;")
    c.execute("""CREATE TABLE job_attempt
        (jaid INTEGER PRIMARY KEY NOT NULL, jid INTEGER, num INTEGER, rid INTEGER, start_time INTEGER, end_time INTEGER,
        FOREIGN KEY(jid) REFERENCES job(jid),
        FOREIGN KEY(rid) REFERENCES resource(rid));""")
    
    # Intermediate result table
    c.execute("DROP TABLE IF EXISTS intermediate_result;")
    c.execute("""CREATE TABLE intermediate_result
        (irid INTEGER PRIMARY KEY NOT NULL, num INTEGER, score REAL, jid INTEGER, receive_time INTEGER,
        FOREIGN KEY(jid) REFERENCES job(jid));""")

    # Multiple results table
    c.execute("DROP TABLE IF EXISTS multiple_result;")
    c.execute("""CREATE TABLE multiple_result
        (mrid INTEGER PRIMARY KEY NOT NULL, label_order INTEGER, value REAL, receive_time INTEGER, \
            jid INTEGER, irid INTEGER, eid INTEGER, is_last_result INTERGER,
        FOREIGN KEY(jid) REFERENCES job(jid),
        FOREIGN KEY(irid) REFERENCES intermediate_result(irid),
        FOREIGN KEY(eid) REFERENCES experiment(eid));""")

    for username in usernames:
        # currently no specific limitation
        c.execute("INSERT INTO user (name, permission) VALUES (?,?)", (username, "all"))

    _insert_resource(config, "gpu_mapping", c, name, "gpu")
    _insert_resource(config, "node_mapping", c, "remote", "node")
    _insert_resource(config, "aws_mapping", c, "remote", "aws")

    for i in range(cpu):
        c.execute("INSERT INTO resource (name, type, status) VALUES (?,?,?)", (name, "cpu", "free"))
    c.execute("INSERT INTO resource (name, type, status) VALUES (?,?,?)", (name, "passive", "free"))
    conn.commit()
    conn.close()

    # print("\033[93mSQLite3 Database is created at %s\033[0m" % config.get("Auptimizer", "SQLITE_FILE"))
    logger.info("SQLite3 Database is created at %s" % config.get("Auptimizer", "SQLITE_FILE"))


def reset(config):
    """Close on-going jobs/experiment and reset resources without deleting existing results:
    
    :param config: contains ``SQLITE_FILE`` under ``Auptimizer`` section
    :type config: configparser.ConfigParser
    """

    conn = _create_connection(config.get("Auptimizer", "SQLITE_FILE"))
    c = conn.cursor()

    c.execute("UPDATE experiment SET end_time=strftime('%s','now') WHERE end_time ISNULL;")
    c.execute("UPDATE job SET score=-999, end_time=strftime('%s','now') WHERE end_time ISNULL;")
    c.execute("UPDATE resource SET status='free' WHERE status='busy';")
    conn.commit()
    conn.close()


@click.command(name="create Auptimizer database, prefer to use aup.setupdb.reset instead of calling this directly",
               context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--user", default=None, help="username for history tracking")
@click.option("--cpu", default=4, type=click.INT, help="number of CPUs to run parallel")
@click.option("--name", default="localhost", help="resource name, not used")
@click.option("--log", default="info", type=click.Choice(["debug", "info", "warn", "error"]), help="Log level")
# name is no in use.  - all resources are under the name of `localhost`
def main(env_file, user, cpu, name, log):  # pragma: no cover
    """Create database for **Auptimizer** with specified in env.ini file.
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        env_file {str}: Auptimizer environment file
    """
    coloredlogs.install(level=LOG_LEVEL[log],
                        fmt="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")

    user = get_default_username(user)

    config = ConfigParser()
    config.read(env_file)
    create_database(config, [user], cpu, name)


if __name__ == "__main__":
    main()
