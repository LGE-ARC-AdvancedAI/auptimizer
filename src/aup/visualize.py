"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Visualize one experiment result
===============================

:mod:`aup.visualize` is the entry point to visualize the result from an 
experiment ``eid``::

  python -m aup.visualize <eid>

Additional arguments
--------------------

.. program-output:: python3 -m aup.visualize -h
  
"""
import json
import logging
import os

import click
import coloredlogs
import pandas as pd

if "DISPLAY" not in os.environ:
    import matplotlib
    matplotlib.use("AGG")

import matplotlib.pylab as plt

from .utils import get_default_connector

_log_level = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "error": logging.ERROR}

logger = logging.getLogger(__name__)


@click.command(name="Visualize an experiment",context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("eid", type=int)
@click.option("--log", default="info", type=click.Choice(["debug", "info", "warn", "error"]))
@click.option("--scale", default="linear", type=click.Choice(['linear', 'log']), help="Scale for y")
@click.option("--save", default=None, type=str, help="output file")
def main(eid, log, scale, save):
    """Visualize result for experiment
    \b\n
    Copyright (C) 2018  LG Electronics Inc.
    \b\n
    GPL-3.0 License. This program comes with ABSOLUTELY NO WARRANTY;
    \b\n
    Arguments:
        eid {int} -- Experiment ID
    """
    coloredlogs.install(level=_log_level[log], fmt="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")
    sql = get_default_connector()
    sql.cursor.execute("SELECT * FROM experiment where eid = ?", (eid,))
    experiment_config = json.loads(sql.cursor.fetchone()[4])

    history = sql.get_all_history(eid)
    history = pd.DataFrame(history)
    history.columns = ['jid', 'score', 'eid', 'rid', 'start_time', 'end_time', 'job_config']

    fig = plt.figure(figsize=(16, 8))
    fig.suptitle("Search Algorithm %s" % experiment_config['proposer'])
    plt.subplot(121)
    plt.plot(history.score)
    plt.legend()
    plt.xlabel("Iteration")
    plt.ylabel("Accuracy")
    plt.yscale(scale)

    plt.subplot(122)
    if experiment_config["target"] == "min":
        plt.plot(history.score.cummin())
        job = history.loc[history.score.idxmin()]
    else:
        plt.plot(history.score.cummax())
        job = history.loc[history.score.idxmax()]
    plt.legend()
    plt.xlabel("Iteration")
    plt.ylabel("Best Accuracy so far")
    plt.yscale(scale)

    print("Best score is %f with config %s" % (job.score, job.job_config))
    if save:
        plt.savefig(save)
    else:
        plt.show()


if __name__ == "__main__":
    main()
