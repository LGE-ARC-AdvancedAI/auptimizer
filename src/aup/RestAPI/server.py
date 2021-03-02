"""
RestAPI server using Flask
============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

from flask import render_template, jsonify, request
from flask_cors import CORS
import connexion
import click
import logging
import sys
import sqlite3 as sql
import os
import os.path
from six.moves.configparser import ConfigParser
import json
import signal
import multiprocessing

from aup.compression.utils import SERIALIZATION_SEPARATOR, run_non_automatic_experiment, verify_compression_config, adjust_compression_config
from aup.setup import setup
from aup.utils import get_default_username, set_default_keyvalue
from ..ET.Connector.SQLiteConnector import SQLiteConnector

from ..EE.Experiment import Experiment
from ..aup import BasicConfig
from aup.Proposer import get_proposer

from threading import Lock

logger = logging.getLogger("RestAPI")

# Create the application instance
app = connexion.App(__name__, specification_dir='./')
CORS(app.app)

EXPS = dict()
EXPS_lock = Lock()

EXPERIMENT_STATUS_TRANSLATE_DICT = {
    "CREATED": "CREATED",
    "RUNNING": "RUNNING",
    "STOPPED": "STOPPED",
    "FINISHED": "FINISHED",
    "FAILED": "FAILED",
    "STOPPING": "STOPPING",
    "REQUEST_STOP": "STOPPING",
    None: None
}


def fix_none_res(arg, value):
    return arg if arg is not None and arg != 'None' else value

def get_display_names(params, exp_config=None, eid=None, cur=None):
    if exp_config is None and eid is not None and cur is not None:
        cur.execute("SELECT json_extract(exp_config, '$') as exp_config \
                            FROM experiment WHERE eid={eid} LIMIT 1;".format(eid=eid))
        exp_config = json.loads(str(cur.fetchone()[0]))
    display_names = {}
    for param in params:
        param = param['name']
        full_param = param.split(SERIALIZATION_SEPARATOR)
        index = int(full_param[0])
        original_key = full_param[-1]
        cdict = exp_config['compression']['config_list'][index]
        for part in full_param[1:-1]:
            cdict = cdict[part]
        if 'op_names' in exp_config['compression']['config_list'][index]:
            new_key = '{} ({})'.format(
                SERIALIZATION_SEPARATOR.join(full_param[1:]),
                ", ".join([op_name for op_name in exp_config['compression']['config_list'][index]['op_names']]))
        else:
            new_key = '{} ({})'.format(
                SERIALIZATION_SEPARATOR.join(full_param[1:]),
                ", ".join([op_type for op_type in exp_config['compression']['config_list'][index]['op_types']]))
        display_names[param] = new_key
    return display_names

def fix_compression_job_config(jobs, params, display_names):
    new_jobs = []
    for job in jobs:
        if job['job_config'] is None:
            new_job = {
                **{display_names[param['name']]: None for param in params},
                **{key: val for key, val in job.items() if key != 'job_config'},
            }
            new_jobs += [new_job]
            continue
        new_job = {key: val for key, val in job.items() if key != 'job_config'}
        job_config = json.loads(job['job_config'])
        for param in params:
            param = param['name']
            full_param = param.split(SERIALIZATION_SEPARATOR)
            index = int(full_param[0])
            original_key = full_param[-1]
            cdict = job_config['config_list'][index]
            for part in full_param[1:-1]:
                cdict = cdict[part]
            new_job[display_names[param]] = cdict[original_key]
        new_jobs += [new_job]
    return new_jobs

def is_compression_experiment(exp_config=None, eid=None, cur=None):
    if exp_config is not None:
        return "compression" in exp_config
    elif eid is not None:
        ret = query_db(cur, "SELECT (json_extract(exp_config, '$.compression') IS NOT NULL) as is_compression_exp \
                            FROM experiment WHERE eid={eid} LIMIT 1;".format(eid=eid))
        return bool(ret[0]["is_compression_exp"])
    else:
        raise ValueError("Missing parameter for is_compression_experiment")

def get_params_for_experiment(cur, eid):
    exp_config = query_db(cur, "SELECT json_extract(exp_config, '$.parameter_config') as parameters from experiment where eid={eid};".format(eid=eid))
    params_json = json.loads(exp_config[0]['parameters'])
    params = []
    for v in params_json:
        name = v['name']
        new_param = {}
        new_param['name'] = name
        new_param['type'] = v['type']
        new_param['range'] = v.get('range', None)
        new_param['interval'] = v.get('interval', None)
        new_param['n'] = v.get('n', None)
        params.append(new_param)
    return params

def query_db(cur, query, args=(), one=False):
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    return (r[0] if r else None) if one else r

def start_experiment_daemon(json_conf, eid, cwd, event):
    daemon_logger = logging.getLogger("RestAPIDaemon")

    is_compression_exp = "compression" in json_conf
    is_one_shot_compression_exp = is_compression_exp and "proposer" not in json_conf

    rc = 0
    exp = None

    previous_dir = os.getcwd()
    os.chdir(cwd)
    try:
        os.setsid()
        os.umask(0)

        if is_compression_exp:
            json_conf = verify_compression_config(json_conf)
            json_conf["compression"] = adjust_compression_config(json_conf["compression"])
            set_default_keyvalue("workingdir", cwd, json_conf, log=logger)
        
        if not is_one_shot_compression_exp:
            exp = Experiment(json_conf, eid=eid)
            exp.add_suspend_signal()
            exp.add_refresh_signal()
        else:
            _, finish = run_non_automatic_experiment(json_conf, os.path.join(".aup"), eid=eid)

        event.set()
        event.clear()
        event.wait()

        if not is_one_shot_compression_exp:
            exp.start()
    except Exception as e:
        daemon_logger.exception('Exception caught:' + str(e))
        rc = 1
    finally:
        if not is_one_shot_compression_exp:
            exp.finish()
        else:
            finish()
        os.chdir(previous_dir)
        os._exit(rc)

def get_valid_jobs_interval(cursor, eid):
    fin_cond = "(score is not NULL and (score == 'EARLY STOPPED' or typeof(score)=='real')) \
                    and start_time is not NULL and end_time is not NULL"

    cursor.execute("SELECT jid, ({fin_cond}) AS stat FROM job WHERE \
                eid={eid} ORDER BY jid;".format(fin_cond=fin_cond, eid=eid))
    sql_res = cursor.fetchall()

    first = None
    last = None
    idx = None
    num_jobs = 0

    for i in range(0, len(sql_res)):
        if first == None and sql_res[i][1] == 1:
            first = sql_res[i][0]
            idx = i
        if first != None and sql_res[i][1] == 0:
            last = sql_res[i-1][0]
            num_jobs = (i - idx)
            break

    start_job = first
    if first == None:
        num_jobs = 0
    elif last == None:
        num_jobs = len(sql_res)

    return (start_job, num_jobs)

# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template('home.html')

@app.route('/api/resource_types', methods=['GET'])
def get_resource_types():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        cur.execute("SELECT DISTINCT type from resource;")
        res = [i[0] for i in cur.fetchall()]
        return jsonify({'resources': res})
    return None

@app.route('/api/experiments/<int:eid>', methods=['GET'])
def get_experiment(eid):
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        experiment = query_db(cur, "SELECT *, json_extract(exp_config, '$.name') as experiment_name, \
                                        json_extract(exp_config, '$.script') as script_name \
                                    from experiment where eid={eid};".format(eid=eid))
        experiment[0]['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[experiment[0].get('status', None)]
        cur = con.cursor()
        cur.execute("SELECT count(*) from job where (end_time is NULL or \
                    (typeof(score) is not 'real' and score is not 'EARLY STOPPED')) and eid={eid}".format(eid=eid))
        unfinished = int(cur.fetchone()[0])
        cur.execute("SELECT count(*) from job where (end_time is not NULL and \
                    (typeof(score) is 'real' or score is 'EARLY STOPPED')) and eid={eid}".format(eid=eid))
        finished = int(cur.fetchone()[0])

        cur.execute("SELECT json_extract(exp_config, '$.target') from experiment where eid={eid}".format(eid=eid))
        order = str(cur.fetchone()[0])
        order = fix_none_res(order, 'max')

        cur.execute("SELECT json_extract(exp_config, '$.proposer') from experiment where eid={eid}".format(eid=eid))
        proposer = str(cur.fetchone()[0])

        cur = con.cursor()
        cur.execute("SELECT exp_config \
                    from experiment where eid={eid};".format(eid=eid))
        exp_config = json.loads(str(cur.fetchone()[0]))
        num_params = len(exp_config['parameter_config'])

        proposer_obj = None
        n_samples = 1
        if proposer is not None and proposer != 'None':
            proposer_obj = get_proposer(proposer)
            n_samples = proposer_obj(exp_config).nSamples

        if proposer == 'bohb' and experiment[0]['status'] == 'FINISHED':
            n_samples = finished

        param_names = []
        for p in range(0, num_params):
            cur.execute("SELECT json_extract(exp_config, '$.parameter_config[{idx}].name') \
                            from experiment where eid={eid};".format(idx=p, eid=eid))
            param_names.append(str(cur.fetchone()[0]))

        is_compression_exp = is_compression_experiment(exp_config)
        best_metrics_vs_hparams = query_db(cur, "SELECT {order}(score) as score, job_config \
                            from job where eid={eid} and typeof(score) = 'real';".format(order=order, eid=eid))

        params = get_params_for_experiment(cur, eid)

        new_best_score = {}

        best_job_config = best_metrics_vs_hparams[0]['job_config']
        if is_compression_exp:
            display_names = get_display_names(params, exp_config)
            best_metrics_vs_hparams = fix_compression_job_config(best_metrics_vs_hparams, params, display_names)
            for param in params:
                if param['name'] in display_names:
                    param['name'] = display_names[param['name']]
                param['value'] = best_metrics_vs_hparams[0][param['name']]
        else: 
            job_configs = [
                json.loads(mvh["job_config"]) if "job_config" in mvh and mvh["job_config"] is not None else {}
                for mvh in best_metrics_vs_hparams
            ]
            best_metrics_vs_hparams = [{
                "score": mvh["score"],
                **{param['name']: job_config[param['name']] if param['name'] in job_config else None for param in params},
            } for mvh, job_config in zip(best_metrics_vs_hparams, job_configs)]

            for param in params:
                param['value'] = best_metrics_vs_hparams[0][param['name']]

        new_best_score['params'] = params
        new_best_score['proposer'] = proposer
        new_best_score['score'] = best_metrics_vs_hparams[0]['score']

        res = {
            'experiment': experiment[0], 
            'best_score': new_best_score,
            'job_stats': {
                'finished': finished, 
                'unfinished': unfinished, 
                'total': n_samples
            },
        }

        if is_compression_exp and len(params) == 0:
            best_config_list = query_db(cur, "SELECT json_extract(exp_config, '$.compression.config_list') as 'config_list' \
                                         FROM experiment WHERE eid={eid} LIMIT 1;".format(eid=eid))
            best_config_list = best_config_list[0]['config_list']
            res['best_score'] = {
                'score': res['best_score']['score'],
                'config_list': best_config_list,
            }

        return res

    return None

@app.route('/api/experiments', methods=['GET'])
def get_experiments():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        experiment = query_db(cur, "SELECT *, json_extract(exp_config, '$.script') as script_name, \
                                    json_extract(exp_config, '$.name') as experiment_name, \
                                    (SELECT case when (SELECT json_extract(exp_config, '$.target') from experiment where eid=experiment.eid) is \"min\" \
                                    then min(score) else max(score) end from job where job.eid=experiment.eid and typeof(score) is 'real') as best_score, \
                                    (SELECT json_group_array(job.score) from job where job.eid=experiment.eid) as scores, \
                                    (SELECT count(*) from job where (end_time is NULL or typeof(score) is not 'real') and job.eid=experiment.eid) as jobs_unfinished, \
                                    (SELECT count(*) from job where end_time is not NULL and typeof(score) = 'real' and job.eid=experiment.eid) as jobs_finished, \
                                    (SELECT json_group_array(json_object('jid', jid, 'score', score, \
                                        'start_time', start_time, 'end_time', end_time, 'job_config', job_config)) from \
                                    (SELECT * from job where eid=experiment.eid order by end_time)) as jobs \
                                    from experiment order by start_time DESC;")
        for e in experiment:
            e['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[e.get('status', None)]

        mult_res_labels = query_db(cur, "SELECT JSON_EXTRACT(exp_config, '$.resource_args.multi_res_labels') \
                                        AS labels FROM experiment ORDER BY start_time DESC")

        list_mult_res_labels = None
        if mult_res_labels is not None:
            for i in range(len(mult_res_labels)):
                labels_str = mult_res_labels[i]['labels']
                if labels_str is None:
                    continue

                list_mult_res_labels = json.loads(labels_str)
                experiment[i]['labels'] = list_mult_res_labels

        resource = query_db(cur, "SELECT * FROM resource WHERE type IS NOT 'passive';")
        return jsonify({'experiment': experiment, 'resource': resource})
    return None

@app.route('/api/job_status', methods=['GET'])
def get_job_status():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        eid = request.args.get('eid')
        job = query_db(cur, "SELECT *, case when end_time is NULL then \"running\" \
                                else \"finished\" end as status, (SELECT rid from job_attempt where jid=job.jid) as rid \
                                from job where eid={eid} order by {sortby} {ASC};".format(eid=eid, \
                        sortby=request.args.get('sortby'), \
                        ASC="ASC" if int(request.args.get('asc')) else "DESC"))
        mult_res_labels = query_db(cur, "SELECT JSON_EXTRACT(exp_config, '$.resource_args.multi_res_labels') AS labels \
                                    FROM experiment WHERE eid=?", (eid,))
        mult_res_labels = mult_res_labels[0]

        list_mult_res_labels = None
        if mult_res_labels is not None and mult_res_labels['labels'] is not None:
            list_mult_res_labels = json.loads(mult_res_labels['labels'])

            for j in job:
                m_res = query_db(cur, "SELECT * FROM multiple_result WHERE jid=? AND is_last_result=1 ORDER BY mrid", (j['jid'],))

                # take the last results
                if len(m_res) < len(list_mult_res_labels):
                    continue
                for res in m_res:
                    j[list_mult_res_labels[res['label_order']-1]] = res['value']

        is_compression_exp = is_compression_experiment(cur=cur, eid=eid)
        if len(job) > 0 and is_compression_exp:
            params = get_params_for_experiment(cur, eid)
            display_names = get_display_names(params, eid=eid, cur=cur)
            job_configs = fix_compression_job_config([{'job_config': j['job_config']} for j in job], params, display_names)
            job = [{
                'job_config': json.dumps(job_configs[idx]),
                **{key: val for key, val in j.items() if key != 'job_config'}
            } for idx, j in enumerate(job)]
        return jsonify({'job': job, 'mult_res_labels': list_mult_res_labels})
    return None

@app.route('/api/hps_space', methods=['GET'])
def get_hps_space():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        eid = request.args.get('eid')
        exp_config = query_db(cur, "SELECT json_extract(exp_config, '$.parameter_config') as parameters, \
                        json_extract(exp_config, '$.proposer') as proposer, \
                        json_extract(exp_config, '$.n_samples') as num_samples from experiment where eid={eid};".format(eid=eid))
        return jsonify({'exp_config': exp_config[0]})
    return None

@app.route('/api/experiment_history', methods=['GET'])
def get_experiment_history():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        experiment_history = query_db(cur, "SELECT *, (SELECT rid from job_attempt where jid=job.jid) as rid from job \
                    where eid={eid} order by end_time;".format(eid=request.args.get('eid')))
        return jsonify({'experiment_history': experiment_history})
    return None

@app.route('/api/experiment_history_best/<int:eid>', methods=['GET'], defaults={'label': None})
@app.route('/api/experiment_history_best/<int:eid>/<label>', methods=['GET'])
def get_experiment_history_best(eid, label):
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        sortby = request.args.get('sortby', 'jid')
        cur = con.cursor()
        cur.execute("SELECT json_extract(exp_config, '$.target') from experiment where eid={eid};".format(eid=eid))
        order = str(cur.fetchone()[0])
        order = fix_none_res(order, 'max')

        list_mult_res_labels = None
        label_order = None
        if label is not None:
            mult_res_labels = query_db(cur, "SELECT JSON_EXTRACT(exp_config, '$.resource_args.multi_res_labels') AS labels \
                                        FROM experiment WHERE eid=?", (eid,))
            mult_res_labels = mult_res_labels[0]

            if mult_res_labels is not None and mult_res_labels['labels'] is not None:
                list_mult_res_labels = json.loads(mult_res_labels['labels'])
                try:
                    label_order = list_mult_res_labels.index(label)+1
                except ValueError:
                    return jsonify({'experiment_history_best': []})

            if list_mult_res_labels is None:
                return jsonify({'experiment_history_best': []})

        (start_job, num_jobs) = get_valid_jobs_interval(cur, eid)

        result = []
        for i in range(1, num_jobs+1):
            best_job = None
            if label is None:
                best_job = query_db(cur, "SELECT jid, {order}(score) as score, job_config from \
                            (SELECT * from job where eid={eid} and jid >= {start_job} order by {sortby} limit 0,{start}) \
                            WHERE typeof(score) == 'real';". \
                            format(order=order, eid=eid, start=i, sortby=sortby, start_job=start_job))
            elif list_mult_res_labels is not None and label_order is not None:
                if sortby == 'end_time':
                    sortby = 'receive_time'
                best_job = query_db(cur, "SELECT jid, {order}(value) as score, (SELECT job_config FROM job WHERE jid=jidm) as job_config FROM \
                                    (SELECT *, jid AS jidm FROM multiple_result WHERE eid={eid} AND \
                                    jid >= {start_job} AND label_order={label_order} AND is_last_result=1 ORDER BY {sortby} LIMIT 0,{start})". \
                                    format(order=order, eid=eid, start=i, start_job=start_job, label_order=label_order, sortby=sortby))
            if best_job is not None and best_job[0]['jid'] is None:
                continue

            is_compression_exp = is_compression_experiment(cur=cur, eid=eid)
            if is_compression_exp:
                params = get_params_for_experiment(cur, eid)
                display_names = get_display_names(params, eid=eid, cur=cur)
                job_configs = fix_compression_job_config([{"job_config": job["job_config"]} for job in best_job], params, display_names)
                best_job = [{
                    "job_config": json.dumps(job_configs[idx]),
                    **{key: val for key, val in job.items() if key != "job_config"}
                } for idx, job in enumerate(best_job)]
            result.append(best_job[0])
        return jsonify({'experiment_history_best': result})
    return None

@app.route('/api/experiment_history_best', methods=['GET'], defaults={'label': None})
@app.route('/api/experiment_history_best/<label>', methods=['GET'])
def get_experiments_history_best(label):
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        sortby = request.args.get('sortby', 'jid')
        cur = con.cursor()
        eids = query_db(cur, "SELECT eid from experiment;")
        result = dict()
        for eid in eids:
            eid = eid['eid']
            cur.execute("SELECT json_extract(exp_config, '$.target') from experiment where eid={eid};".format(eid=eid))
            order = str(cur.fetchone()[0])
            order = fix_none_res(order, 'max')

            list_mult_res_labels = None
            label_order = None
            if label is not None:
                mult_res_labels = query_db(cur, "SELECT JSON_EXTRACT(exp_config, '$.resource_args.multi_res_labels') AS labels \
                                            FROM experiment WHERE eid=?", (eid,))
                mult_res_labels = mult_res_labels[0]

                if mult_res_labels is not None and mult_res_labels['labels'] is not None:
                    list_mult_res_labels = json.loads(mult_res_labels['labels'])
                    try:
                        label_order = list_mult_res_labels.index(label)+1
                    except ValueError:
                        continue

                if list_mult_res_labels is None:
                    continue

            (start_job, num_jobs) = get_valid_jobs_interval(cur, eid)

            result[eid] = list()
            for i in range(1, num_jobs+1):
                best_job = None
                if label is None:
                    best_job = query_db(cur, "SELECT jid, {order}(score) as score, job_config, start_time, end_time from \
                                (SELECT * from job where eid={eid} and jid >= {start_job} order by {sortby} limit 0,{start}) \
                                WHERE typeof(score) == 'real';". \
                                format(order=order, eid=eid, start=i, sortby=sortby, start_job=start_job))
                elif list_mult_res_labels is not None and label_order is not None:
                    if sortby == 'end_time':
                        sortby = 'receive_time'
                    best_job = query_db(cur, "SELECT jid, {order}(value) as score, (SELECT job_config FROM job WHERE jid=jidm) as job_config FROM \
                                        (SELECT *, jid AS jidm FROM multiple_result WHERE eid={eid} AND \
                                        jid >= {start_job} AND label_order={label_order} AND is_last_result=1 ORDER BY {sortby} LIMIT 0,{start})". \
                                        format(order=order, eid=eid, start=i, start_job=start_job, label_order=label_order, sortby=sortby))
                if best_job is not None and best_job[0]['jid'] is None:
                    continue

                is_compression_exp = is_compression_experiment(cur=cur, eid=eid)
                if is_compression_exp:
                    params = get_params_for_experiment(cur, eid)
                    display_names = get_display_names(params, eid=eid, cur=cur)
                    job_configs = fix_compression_job_config([{"job_config": job["job_config"]} for job in best_job], params, display_names)
                    best_job = [{
                        "job_config": json.dumps(job_configs[idx]),
                        **{key: val for key, val in job.items() if key != "job_config"}
                    } for idx, job in enumerate(best_job)]

                result[eid].append(best_job[0])
        return jsonify({'experiment_history_best': result})
    return None

@app.route('/api/experiment_comparison_best', methods=['GET'])
def get_experiment_comparison_best():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        eid = request.args.get('eid')
        cur = con.cursor()
        cur.execute("SELECT json_extract(exp_config, '$.target') from experiment where eid={eid}".format(eid=eid))
        order = str(cur.fetchone()[0])
        order = fix_none_res(order, 'max')
        result = query_db(cur, "SELECT jid, {order}(score), job_config from job where eid={eid};" \
                        .format(order=order, eid=eid))
        return jsonify({'experiment_comparison_best': result})
    return None

@app.route('/api/metrics_vs_hparams', methods=['GET'])
def get_metrics_vs_hparams():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        eid = int(request.args.get('eid'))
        cur = con.cursor()

        params = get_params_for_experiment(cur, eid)

        metrics_vs_hparams = query_db(cur, "SELECT score, job_config from job \
                            where eid={eid} and typeof(score) == 'real';".format(eid=eid))
        is_compression_exp = is_compression_experiment(cur=cur, eid=eid)

        if is_compression_exp:
            display_names = get_display_names(params, eid=eid, cur=cur)
            metrics_vs_hparams = fix_compression_job_config(metrics_vs_hparams, params, display_names)
        else:
            metrics_vs_hparams = [{
                "score": mvh["score"],
                **{key: val for key, val in json.loads(mvh["job_config"]).items()},
            } for mvh in metrics_vs_hparams]

        return jsonify({'metrics_vs_hparams': metrics_vs_hparams})
    return None

@app.route('/api/experiments_status')
def get_experiment_status():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        result = query_db(cur, "SELECT eid, start_time, end_time, status \
                                FROM experiment;")
        for r in result:
            r['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[r['status']]
        return jsonify({'experiments_status': result})
    return None

@app.route('/api/job_stats/<int:eid>')
def get_job_stats(eid):
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        cur.execute("SELECT count(*) from job where end_time is NULL and eid={eid}".format(eid=eid))
        unfinished = int(cur.fetchone()[0])
        cur.execute("SELECT count(*) from job where end_time is not NULL and eid={eid}".format(eid=eid))
        finished = int(cur.fetchone()[0])

        return jsonify({'finished': finished, 'unfinished': unfinished})
    return None

@app.route('/api/current_db', methods=['GET'])
def get_current_db():
    db_path = app.app.config['db_file']
    return jsonify({'db_path': os.path.abspath(db_path) if db_path is not None else None})

@app.route('/api/setup', methods=['POST'])
def perform_setup():
    if request.method == 'POST':
        data = request.json

        work_dir = data.get('work_dir')

        previous_dir = os.getcwd()
        try:
            os.chdir(work_dir)

            ini_path = data.get('ini_path')

            cpu = data.get('cpu', '4')
            cpu = int(cpu)

            aws_file = data.get('aws_file', 'none')
            gpu_file = data.get('gpu_file', 'none')
            node_file = data.get('node_file', 'none')

            if not os.path.exists(ini_path):
                raise Exception("{} does not exist".format(ini_path))
            if aws_file is not 'none' and (not os.path.exists(aws_file)):
                raise Exception("{} does not exist".format(aws_file))
            if gpu_file is not 'none' and (not os.path.exists(gpu_file)):
                raise Exception("{} does not exist".format(gpu_file))
            if node_file is not 'none' and (not os.path.exists(node_file)):
                raise Exception("{} does not exist".format(node_file))

            overwrite = data.get('overwrite', 'False')
            overwrite = bool(overwrite) 

            user = data.get('user')

            config = ConfigParser()
            config.optionxform = str

            config.read(ini_path)
            user = get_default_username(user)
            setup(config, cpu, gpu_file, node_file, aws_file, user, overwrite, 'info')

            app.app.config['db_file'] = os.path.join(work_dir, config.get("Auptimizer", "Auptimizer_PATH"), 'sqlite3.db')
        except Exception as e:
            logger.fatal('Exception caught:' + str(e))
            return jsonify(isError=True,
                    message=str(e),
                    statusCode=500), 500
        finally:
            os.chdir(previous_dir)

        return jsonify(isError= False,
                    message= "Success",
                    statusCode=200), 200

@app.route('/api/create_experiment', methods=['POST'])
def create_experiment():
    if request.method == 'POST':
        data = request.json

        cwd = data.get('cwd', None)
        json_config_body = data.get('json_config_body', None)

        is_compression_exp = "compression" in json_config_body
        is_automatic_compression_exp = is_compression_exp and "proposer" in json_config_body

        try:
            previous_dir = os.getcwd()
            os.chdir(cwd)

            config = BasicConfig()
            config.update(json_config_body)

            config['cwd'] = cwd

            if is_compression_exp:
                config = verify_compression_config(config)
                config["compression"] = adjust_compression_config(config["compression"])
                set_default_keyvalue("workingdir", cwd, config, log=logger)

            if is_compression_exp and not is_automatic_compression_exp:
                eid, _ = run_non_automatic_experiment(config, os.path.join(".aup"), start=False)
            else:
                e = Experiment(config, start=False)
                eid = e.eid

            os.chdir(previous_dir)

            with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
                cur = con.cursor()
                experiment = query_db(cur, "SELECT *, json_extract(exp_config, '$.name') as experiment_name, \
                                                            json_extract(exp_config, '$.script') as script_name \
                                                        from experiment where eid={eid};".format(eid=eid))
                experiment = experiment[0]
                experiment['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[experiment['status']]
            return jsonify(experiment)
        except Exception as e:
            os.chdir(previous_dir)
            logger.exception('Exception caught:' + str(e))
            return jsonify(isError=True,
                message=str(e),
                statusCode=500), 500

@app.route('/api/start_experiment', methods=['POST'])
def start_experiment():
    if request.method == 'POST':
        data = request.json

        eid = int(data.get('eid', -1))
        cwd = None

        json_conf = None

        with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
            cur = con.cursor()
            cur.execute("SELECT exp_config from experiment where eid={eid};".format(eid=eid))

            json_conf = BasicConfig()
            json_conf.update(json.loads(cur.fetchone()[0]))

            cur.execute("SELECT json_extract(exp_config, '$.cwd') from experiment where eid={eid};".format(eid=eid))
            cwd = str(cur.fetchone()[0])

        init_exp_event = None

        try:
            init_exp_event = multiprocessing.Event()
            proc = multiprocessing.Process(target=start_experiment_daemon,
                    args=(json_conf, eid, cwd, init_exp_event))
            proc.daemon = True

            proc.start()

            with EXPS_lock:
                EXPS[eid] = (proc, cwd)
            init_exp_event.wait()

            with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
                cur = con.cursor()
                experiment = query_db(cur, "SELECT *, json_extract(exp_config, '$.name') as experiment_name, \
                                                    json_extract(exp_config, '$.script') as script_name \
                                                from experiment where eid={eid};".format(eid=eid))
                experiment = experiment[0]
                experiment['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[experiment['status']]
            # let daemon start the experiment after we finished with the db
            init_exp_event.set()
            return jsonify(experiment)
        except Exception as e:
            logger.exception('Exception caught:' + str(e))
            return jsonify(isError=True,
                message= "Exception occurred:" + str(e),
                statusCode=500), 500

@app.route('/api/stop_experiment', methods=['POST'])
def stop_experiment():
    if request.method == 'POST':
        data = request.json

        eid = int(data.get('eid', -1))

        try:
            with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
                cur = con.cursor()
                experiment = query_db(cur, "UPDATE experiment SET status = 'REQUEST_STOP' \
                                            WHERE eid={eid}".format(eid=eid))
            
            with EXPS_lock:
                if eid in EXPS:
                    # force a last refresh
                    os.kill(EXPS[eid][0].pid, signal.SIGUSR1)
                    del EXPS[eid]
            
            with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
                cur = con.cursor()
                experiment = query_db(cur, "SELECT *, json_extract(exp_config, '$.name') as experiment_name, \
                                                        json_extract(exp_config, '$.script') as script_name \
                                                    from experiment where eid={eid};".format(eid=eid))
                experiment = experiment[0]
                experiment['status'] = EXPERIMENT_STATUS_TRANSLATE_DICT[experiment['status']]
                return jsonify(experiment)
        except Exception as e:
            logger.exception('Exception caught:' + str(e))
            return jsonify(isError=True,
                message= "Exception occurred:" + str(e),
                statusCode=500), 500

@app.route('/api/refresh_all', methods=['POST'])
def refresh_all():
    try:
        to_delete = list()

        with EXPS_lock:
            for k, v in EXPS.items():
                if v[0].exitcode == None:
                    os.kill(v[0].pid, signal.SIGUSR1)
                else:
                    to_delete.append(k)
            for eid in to_delete:
                del EXPS[eid]

        return jsonify(isError= False,
                        message= "Success",
                        statusCode=200), 200
    except Exception as e:
        logger.exception('Exception caught:' + str(e))
        return jsonify(isError=True,
            message= "Exception occurred:" + str(e),
            statusCode=500), 500

@app.route('/api/interm_res', methods=['GET'])
def get_interm_res():
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        experiments = query_db(cur, "SELECT * from experiment WHERE \
                                     JSON_EXTRACT(exp_config, '$.resource_args.track_intermediate_results') = 1")

        res = list()
        for exp in experiments:
            obj = dict()

            eid = int(exp['eid'])
            name = str(exp['name'])
            script_name = str(json.loads(exp['exp_config'])['script'])

            obj['eid'] = eid
            obj['name'] = name
            obj['scriptName'] = script_name

            res.append(obj)

        return jsonify(res)

@app.route('/api/interm_res/<int:eid>', methods=['GET'], defaults={'label': None})
@app.route('/api/interm_res/<int:eid>/<label>', methods=['GET'])
def get_interm_res_by_eid(eid, label):
    with sql.connect(app.app.config['db_file'], check_same_thread=False) as con:
        cur = con.cursor()
        res = query_db(cur, "SELECT * from experiment WHERE \
                             JSON_EXTRACT(exp_config, '$.resource_args.track_intermediate_results') = 1 AND eid={eid}".format(eid=eid))

        if len(res) == 0:
            return jsonify(dict())

        exp = res[0]
        name = str(exp['name'])
        script_name = str(json.loads(exp['exp_config'])['script'])

        obj = dict()

        list_mult_res_labels = None
        label_order = None

        mult_res_labels = query_db(cur, "SELECT JSON_EXTRACT(exp_config, '$.resource_args.multi_res_labels') AS labels \
                                    FROM experiment WHERE eid=?", (eid,))
        mult_res_labels = mult_res_labels[0]

        if mult_res_labels is not None and mult_res_labels['labels'] is not None:
            list_mult_res_labels = json.loads(mult_res_labels['labels'])
            if label is not None:
                label_order = list_mult_res_labels.index(label)+1
            obj['multResLabels'] = list_mult_res_labels

        obj['eid'] = eid
        obj['name'] = name
        obj['scriptName'] = script_name
        obj['jobs'] = list()

        jids = query_db(cur, "SELECT jid from job WHERE \
                        eid={eid}".format(eid=eid))
        for jid in jids:
            field = dict()

            jid_int = int(jid['jid'])

            field['jid'] = jid_int
            field['interimResults'] = list()

            interm_res = None

            if label is None:
                interm_res = query_db(cur, "SELECT * from intermediate_result WHERE \
                                jid={jid} ORDER BY receive_time".format(jid=jid_int))
            elif list_mult_res_labels is not None and label_order is not None:
                interm_res = query_db(cur, "SELECT *, value as score FROM multiple_result WHERE\
                                        jid={jid} and label_order={label_order} ORDER BY receive_time".\
                                        format(jid=jid_int, label_order=label_order))

            for in_res in interm_res:
                field['interimResults'].append({"irid": in_res['irid'], "receiveTime": in_res['receive_time'], "score": in_res['score']})

            obj['jobs'].append(field)

        return jsonify(obj)

@app.route('/api/experiment/<int:eid>', methods=['DELETE'])
def delete_experiment(eid):
    if eid in EXPS:
         del EXPS[eid]

    conn = SQLiteConnector(app.app.config['db_file'])
    rc = conn.delete_experiment(eid)
    conn.close()

    if not rc:
        return jsonify(isError=True,
            message= "Experiment with eid={eid} not found".format(eid=eid),
            statusCode=500), 500
    else:
        return jsonify(isError=False,
            message="Success",
            statusCode=200), 200

def disable_http_logs(disable):
    if disable:
        import click

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        def secho(text, file=None, nl=None, err=None, color=None, **styles):
            pass

        def echo(text, file=None, nl=None, err=None, color=None, **styles):
            pass
        click.echo = echo
        click.secho = secho

def main(path, port):
    if path is not None and not os.path.exists(path):
        return 1

    app.app.config['db_file'] = os.path.abspath(path) if path is not None else None
    app.app.config['CORS_HEADERS'] = 'Content-Type'

    disable_http_logs(True)

    app.run(host='0.0.0.0', port=int(port), debug=False)

    return 0

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    db_file = None
    port = None

    try:
        if len(sys.argv) == 3:
            db_file = str(sys.argv[1])
            if not os.path.exists(db_file):
                logger.fatal('Db file does not exist')
                exit(1)

            port = int(sys.argv[2])
        elif len(sys.argv) == 2:
            logger.warning("Running without db!")
            port = int(sys.argv[1])
        else:
            logger.fatal('Specify at least a port!')
            exit(1)
    except ValueError as ve:
        logger.fatal('Cannot parse port!:' + str(ve))
        exit(1)
    except Exception as e:
        logger.fatal('Caught exception:' + str(e))
        exit(1)

    app.app.config['db_file'] = os.path.abspath(db_file) if db_file is not None else None
    app.app.config['CORS_HEADERS'] = 'Content-Type'
    app.run(host='0.0.0.0', port=port, debug=False)
