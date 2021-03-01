# Compression examples (Tensorflow)

## Requirements

The basic requirements for Auptimizer apply here.

Additionally, in order for the examples to work, the following packages are required:
* tensorflow >= 2.0

## Running the examples

For non-automatic examples:

```sh
python -m aup.compression exp_fpgm.json
```

For automatic examples:

```sh
python -m aup.compression exp_auto_fpgm.json --automatic
```
The ``--launch_dashboard`` flag can be added to the command if the user wants to show the dashboard while running the experiment.