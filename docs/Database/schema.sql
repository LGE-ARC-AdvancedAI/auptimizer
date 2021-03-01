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
CREATE TABLE job_attempt
        (jaid INTEGER PRIMARY KEY NOT NULL, jid INTEGER, num INTEGER, rid INTEGER, start_time INTEGER, end_time INTEGER,
        FOREIGN KEY(jid) REFERENCES job(jid),
        FOREIGN KEY(rid) REFERENCES resource(rid));
CREATE TABLE intermediate_result
        (irid INTEGER PRIMARY KEY NOT NULL, num INTEGER, score REAL, jid INTEGER, receive_time INTEGER,
        FOREIGN KEY(jid) REFERENCES job(jid));
CREATE TABLE multiple_result
        (mrid INTEGER PRIMARY KEY NOT NULL, label_order INTEGER, value REAL, receive_time INTEGER,
        jid INTEGER, irid INTEGER, eid INTEGER, is_last_result INTERGER,
        FOREIGN KEY(jid) REFERENCES job(jid),
        FOREIGN KEY(irid) REFERENCES intermediate_result(irid),
        FOREIGN KEY(eid) REFERENCES experiment(eid));
