# Rosenbrock demo

## Setup

    python -m aup.setup

To setup different resource configuration, see [resource example](../2dfunc_diff_res/README.md).

## Experiment

    python -m aup experiment_sequence.json --log warn
    python -m aup experiment_random.json
    python -m aup experiment_spearmint.json
    python -m aup experiment_hyperopt.json

Results are presented in [History](History.ipynb)

## Experiment Auto-convert

To convert the original `rosenbrock_origin.py` for *Auptimizer*, users can use

    python -m aup.convert rosenbrock_origin.py experiment_auto.json rosenbrock

It will create `rosenbrock_auto.py` for user to use for *Auptimizer* experiment.

## Reset

To clean the database, use 

    python -m aup.setupdb.reset .aup/env.ini
