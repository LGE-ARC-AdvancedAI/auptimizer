CREATE TABLE user
    (uid INTEGER PRIMARY KEY NOT NULL, name TEXT UNIQUE, permission BLOB);
CREATE TABLE resource
    (rid INTEGER PRIMARY KEY NOT NULL, name TEXT, type TEXT, status TEXT);
CREATE TABLE experiment 
    (eid INTEGER PRIMARY KEY NOT NULL, uid INTEGER, start_time INTEGER, end_time INTEGER, exp_config BLOB,
    FOREIGN KEY(uid) REFERENCES user(uid));
CREATE TABLE job
    (jid INTEGER PRIMARY KEY NOT NULL, score REAL, eid INTEGER, rid INTEGER, start_time INTEGER, end_time INTEGER,
    job_config BLOB,
    FOREIGN KEY(eid) REFERENCES experiment(eid),
    FOREIGN KEY(rid) REFERENCES resource(rid));
