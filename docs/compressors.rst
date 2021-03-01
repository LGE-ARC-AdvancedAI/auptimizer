Supported Compression Algorithms
================================
For a high-level introduction of all NNI pruners and quantizers, and the full list of parameters required for each compression algorithm in ``config_list``,
please refer to `compressors <https://nni.readthedocs.io/en/stable/Compression/Overview.html#supported-algorithms>`__.
We maintain the same parameters for each compression algorithm as in the original NNI compression module.


In this section, we provide examples for all of the supported compression algorithms that include:

+ An example configuration (for one-time compression) to present the required "framework",
  "type" and "compressor" parameters.
+ An example of a``aup.create_compressor`` call. If the compressor supports `"dependency-aware" mode <https://nni.readthedocs.io/en/latest/Compression/DependencyAware.html>`__, 
  it will be included in the call.

Pruners
-------

Level Pruner
~~~~~~~~~~~~

Supports both TensorFlow and PyTorch.

**Configuration**::

    "compression": {
        "framework": "tensorflow" | "torch"
        "type": "pruning",
        "compressor": "level",
        "config_list": [{
                "sparsity": 0.8,
                "op_types": ["default"]
            }
        ]
    }

**Example creation**::

    aup.create_compressor(model, config, optimizer=None)

Slim Pruner
~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "slim",
        "config_list": [{
                "sparsity": 0.8,
                "op_types": ["BatchNorm2d"]
            }
        ]
    }

**Example creation**::

    aup.create_compressor(model, config, optimizer=None)

FPGM Pruner
~~~~~~~~~~~

This pruner supports a dependency-aware mode to get better speed-up from the pruning. 

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "fpgm",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, dependency_aware=False, dummy_input=None)

L1Filter Pruner
~~~~~~~~~~~~~~~

This pruner supports the dependency-aware mode.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "l1_filter",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }

  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, dependency_aware=False, dummy_input=None)

L2Filter Pruner
~~~~~~~~~~~~~~~

This pruner supports the dependency-aware mode.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "l2_filter",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, dependency_aware=False, dummy_input=None)

ActivationAPoZRankFilter Pruner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pruner supports the dependency-aware mode.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "activation_apoz_rank_filter",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, activation='relu', statistics_batch_num=1, dependency_aware=False, dummy_input=None)

ActivationMeanRankFilter Pruner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pruner supports the dependency-aware mode.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "activation_mean_rank_filter",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, activation='relu', statistics_batch_num=1, dependency_aware=False, dummy_input=None)

TaylorFOWeightFilter Pruner
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This pruner supports the dependency-aware mode.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "taylor_fo_weight_filter",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, statistics_batch_num=1, dependency_aware=False, dummy_input=None)

AGP Pruner
~~~~~~~~~~

**Special requirements for usage** (example)::

    compressor = aup.compression.create_compressor(model, config, optimizer=optimizer)
    model = compressor.compress()

    for epoch in range(1, args.epochs + 1):
        # ... train the model here for one epoch
        compressor.update_epoch(epoch)
 
Use ``compressor.update_epoch(epoch)`` to update epoch number when you finish one epoch in 
your training code.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "agp",
        "config_list": [{    
                "initial_sparsity": 0.0,
                "final_sparsity": 0.8,
                "start_epoch": 0,
                "end_epoch": 10,
                "frequency": 1,
                "op_types": ["default"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer, pruning_algorithm='level')

NetAdapt Pruner
~~~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "net_adapt",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, short_term_fine_tuner, evaluator, optimize_mode='maximize', base_algo='l1', sparsity_per_iteration=0.05, experiment_data_dir='./')

SimulatedAnnealing Pruner
~~~~~~~~~~~~~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "simulated_annealing",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, evaluator, optimize_mode='maximize', base_algo='l1', start_temperature=100, stop_temperature=20, cool_down_rate=0.9, perturbation_magnitude=0.35, experiment_data_dir='./')

AutoCompress Pruner
~~~~~~~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "auto_compress",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, trainer, evaluator, dummy_input, num_iterations=3, optimize_mode='maximize', base_algo='l1', start_temperature=100, stop_temperature=20, cool_down_rate=0.9, perturbation_magnitude=0.35, admm_num_iterations=30, admm_training_epochs=5, row=0.0001, experiment_data_dir='./')

AMC Pruner
~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "amc",
        "config_list": [{
                "op_types": ["Conv2d", "Linear"]
            }
        ]
    }

**Example creation**::

    aup.create_compressor(model, config, evaluator, val_loader, suffix=None, model_type='mobilenet', dataset='cifar10', flops_ratio=0.5, lbound=0.2, rbound=1.0, reward='acc_reward', n_calibration_batches=60, n_points_per_layer=10, channel_round=8, hidden1=300, hidden2=300, lr_c=0.001, lr_a=0.0001, warmup=100, discount=1.0, bsize=64, rmsize=100, window_length=1, tau=0.01, init_delta=0.5, delta_decay=0.99, max_episode_length=1000000000.0, output_dir='./logs', debug=False, train_episode=800, epsilon=50000, seed=None)

ADMM Pruner
~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "admm",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"],
                "op_names": ["conv1"]
            }, {
                "sparsity": 0.5,
                "op_types": ["Conv2d"],
                "op_names": ["conv2"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, trainer, num_iterations=30, training_epochs=5, row=0.0001, base_algo='l1')

Lottery Ticket Hypothesis Pruner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Special requirements for usage** (example)::

    compressor = aup.compression.create_compressor(model, config, optimizer=optimizer, lr_scheduler=scheduler)
    model = compressor.compress()

    for _ in compressor.get_prune_iterations():
        compressor.prune_iteration_start()
        for epoch in range(1, args.epochs + 1):
            # ... train model here for one epoch

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "lottery_ticket",
        "config_list": [{
                "prune_iterations": 5,
                "sparsity": 0.8,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config, optimizer=None, lr_scheduler=None, reset_weights=True)

Sensitivity Pruner
~~~~~~~~~~~~~~~~~~

**Special requirements for usage** (example)::

    compressor = aup.compression.create_compressor(model, config, finetuner=short_term_fine_tuner, evaluator=evaluator)
    model = compressor.compress(eval_args=[model], finetune_args=[model])

Notice the arguments passed to ``compressor.compress``.

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "pruning",
        "compressor": "sensitivity",
        "config_list": [{
                "sparsity": 0.5,
                "op_types": ["Conv2d"]
            }
        ]
    }
  
**Example creation**::

    aup.create_compressor(model, config_list, evaluator, finetuner=None, base_algo='l1', sparsity_proportion_calc=None, sparsity_per_iter=0.1, acc_drop_threshold=0.05, checkpoint_dir=None)

Quantizers
----------

Naive Quantizer
~~~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "quantization",
        "compressor": "naive",
        "config_list": []
    }
  
**Example creation**::

    aup.create_compressor(model, config)

QAT Quantizer
~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "quantization",
        "compressor": "qat",
        "config_list": [{
            "quant_types": ["weight"],
            "quant_bits": {
                "weight": 8
            },
            "op_types": ["Conv2d", "Linear"]
        }, {
            "quant_types": ["output"],
            "quant_bits": 8,
            "quant_start_step": 7000,
            "op_types":["ReLU6"]
        }]
    }

  
**Example creation**::

    aup.create_compressor(model, config)

DoReFa Quantizer
~~~~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "quantization",
        "compressor": "dorefa",
        "config_list": [{
            "quant_types": ["weight"],
            "quant_bits": 8, 
            "op_types": ["default"] 
        }]
    }
  
**Example creation**::

    aup.create_compressor(model, config)

BNN Quantizer
~~~~~~~~~~~~~

**Configuration**::

    "compression": {
        "framework": "torch",
        "type": "quantization",
        "compressor": "bnn",
        "config_list": [{
                "quant_bits": 1,
                "quant_types": ["weight"],
                "op_types": ["Conv2d", "Linear"],
                "op_names": ["conv1", "conv2", "fc1", "fc2"]
            }, {
                "quant_bits": 1,
                "quant_types": ["output"],
                "op_types": ["relu"],
                "op_names": ["relu1", "relu2", "relu3"]
        }]
    }
  
**Example creation**::

    aup.create_compressor(model, config)