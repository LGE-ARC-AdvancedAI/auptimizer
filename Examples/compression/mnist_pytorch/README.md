# Compression examples (PyTorch)

## Requirements

The base requirements for Auptimizer apply here.

Additionally, in order for the examples to work, torch >= 1.7.0 is needed.

## Example details
We provide an example configuration file and a corresponding training script for each of the compressors supported. Due to the fact that some compressors require additional modification of the training script, we provide individual training scripts for those compressors for clarity.

For pruners, we also provide the configuration files for both one-time compression and automatic compression experiments. For one-time compression, the configuration file is named as ``exp_<pruner_name>.json``. For automatic compression, the configuration file is named as ``exp_auto<pruner_name>.json``.  

For quantizers, the configuration file is named as ``exp_<quantizer_name>.json``.

To further demonstrate the usage of automatic compression experiments using different Proposers and hyperparameter settings, we provide multiple examples for each of the Proposer. The corresponding configuration files are named ``exp_auto_fpgm_<Proposer_name>.json``. 

In addition, to showcase the two use cases where the user can assign the same or different hyperparameter values for a group of layers, the configuration files ``exp_auto_fpgm_random_no_expand.json`` and ``exp_auto_fpgm_random.json`` can be used as references comparatively.

Finally, ``exp_auto_fpgm_aup_args.json`` and ``mnist_aup_args.py`` demonstrate how to use the decorator 
``@aup_args`` to launch a compression experiment.

## Running the examples

For one-time compression:

```sh
python -m aup.compression exp_level.json
```

For automatic compression:

```sh
python -m aup.compression exp_auto_level.json --automatic
```

The ``--launch_dashboard`` flag can be added to the command if the user wants to show the dashboard while running the experiment.