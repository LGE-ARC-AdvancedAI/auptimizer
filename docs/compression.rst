Compressor
==========

**Compressor** is a model compression tool that helps reduce memory complexity and inference time of neural networks.

With Compressor, you can:

1. **Make your ML models suitable for deployment on resource-constrained devices.** Use Compressor to optimize models for Edge device's limited memory, compute, or power and enable uncompromised on-device intelligence.
2. **Slash latency and enhance the user experience of your AI-powered application.** Tap Compressor's speed-up functionality to accelerate your model's inference time.
3. **Maximize the cost-effectiveness of your neural nets.** Cut down on cloud or on-prem model storage and compute costs by reducing their footprint.

Similar to Auptimizer-Hyperparameter Optimization (HPO), Compressor aims to provide a unified interface to the existing state-of-the-art toolkits. Currently, Compressor leverages `NNI (version 2.0) <https://nni.readthedocs.io/en/latest/model_compression.html>`__ model compression modules. NNI is an open-source toolkit that supports two types of compression, pruning and quantization, for TensorFlow, and PyTorch models. You can find more detail on supported compression algorithms (compressors) in the `NNI Compression documentation <https://nni.readthedocs.io/en/stable/model_compression.html>`__.

In the future, we will be integrating other off-the-shelf toolkits to expand the selection of model compression approaches.

How to run compression experiments
----------------------------------

Running a compression experiment is similar to running an HPO experiment and requires just a few steps: 

1. Install Auptimizer and set up Auptimizer environment
2. Prepare an experiment configuration file
3. Modify a few lines in the training script 
4. Run the experiment


Auptimizer also includes the NNI `compression utility functions <https://nni.readthedocs.io/en/stable/Compression/CompressionUtils.html>`__ that will help 
you design compression experiments more efficiently. These utility functions enable layer sensitivity 
and channel dependency analysis, which can guide the selection of layers to be pruned and the target 
sparsity levels. We recommend running this analysis to have a better understanding of the model architecture. 
For more details, please check :doc:`Utility functions <compression_utilities>`.

Step #1. Installation and environment setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compressor is automatically installed as a part of Auptimizer. 

For PyTorch compression algorithms, Pytorch version >= 1.7.0 is required. For 
Tensorflow compression algorithms, TensorFlow version >= 2.0 is required. 

Compression experiments use the same Auptimizer environment as the HPO experiments. Please refer
to the :doc:`Install and setup Auptimizer <setup>` and :doc:`Set up environment 
<environment>` sections for detail on how to set up your Auptimizer environment.

Step #2. Prepare an experiment configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compressor supports two compression paradigms: 

1. one-time compression 
2. automatic compression. 

A **one-time compression** experiment runs one compression job with a fixed set of parameters. 
Whereas an **automatic compression** experiment leverages Auptimizer's HPO 
module to find the best possible parameters of a compression algorithm that generates the 
best compressed model. 

One-time approach is a good option for performing a dry-run or an experiment with a specific set of parameters. Alternatively, use automatic compression if you are not certain about 
the compression parameters or would like to explore the relationship between compressed model performance 
and different parameter settings. 

Below, we explain the differences between one-time and automatic compression configuration files.

One-time compression configuration
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Here is an example of the configuration file for one-time compression using the `L1Filter` pruning method::
    
    {
        "name": "MNIST L1 Filter Pruner",
        "script": "mnist.py",
        "resource": "cpu",
        "compression": {
            "framework": "torch",
            "type": "pruning",
            "compressor": "l1_filter",
            "config_list": [
                {
                    "sparsity": 0.8,
                    "op_types": ["Conv2d"]
                },
                {
                    "sparsity": 0.6,
                    "op_names": ["conv1", "conv2"]
                },
                {
                    "exclude": True,
                    "op_names": ["conv3"]
                }
            ]
        }
    }

One-time compression experiment configurations take the following parameters, where all parameters except for **compression**
have the same meaning as in :doc:`Configure HPO Algorithm <algorithm>`:

+ **name**: name of the experiment
+ **script**: script to run
+ **resource**: type of resource to run the experiment, [cpu, gpu, passive, node]
+ **workingdir**: path to run the script, important for running jobs remotely (SSH/AWS)
+ **compression**: compression-specific parameters
    
    + **framework**: either "torch" or "tensorflow"

    + **type**: either "pruning" or "quantization"
    
    + **compressor**: string, one from the list of supported compression algorithms for the given
      framework and type (see below)
    
    + **config_list**: a list of parameters which define the specific requirements for the chosen NNI 
      compression algorithm

The ``config_list`` parameter is specific to individual NNI compression algorithms. However, there a few parameters
common among all compressors:

+ **op_types**: list of strings, the names of the specific type of layers to be compressed.
  If not specified, will use ``default`` as the value which denotes the default layer types 
  supported by the chosen compression algorithm. 
+ **op_names**: list of strings, the names of the layers to be compressed. Will overwrite 
  ``op_types`` if both are provided. The layer names can be found using ``model.state_dict().keys()``. 
+ **exclude**: "True" or "False" (default is "False"). When set to "True", the layers 
  defined in ``op_types`` or ``op_names`` will be excluded from compression.

In the above example, "config_list" means pruning all layers of the type "Conv2d" to 0.8 sparsity, except for
layers named "conv1" and "conv2" which should be pruned to 0.6 sparsity and layer "conv3" which should be 
excluded from the pruning.

Please refer to the `NNI docs <https://nni.readthedocs.io/en/stable/Compression/QuickStart.html#specification-of-config-list>`__
for more description of the "config_list" parameter. Each compressor will have
an example of its supported "config_list".

Automatic compression configuration
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Here is an example of the configuration file for automatic compression using the 
`L1Filter` pruning method::

    {
        "name": "MNIST L1 Filter Pruner (automatic)",
        "script": "mnist.py",
        "resource": "cpu",
        "compression": {
            "framework": "torch",
            "type": "pruning",
            "compressor": "l1_filter",
            "config_list": [
                {
                    "sparsity": {
                        "range": [0.6, 0.8],
                        "type": "float"
                    }
                    "op_types": ['Conv2d']
                },

                {
                    "sparsity": {
                        "range": [0.1, 0.9],
                        "type": "float"
                    },
                    "op_names": ["conv1", "conv2"]
                },

                {
                    "exclude": True,
                    "op_names": ["conv3"]
                }  
            ]
        },
        "proposer": "random",
        "n_parallel": 4,
        "target": "max",
        "n_samples": 4
    }

An automatic compression experiment uses HPO to find the best hyperparameters of a chosen compression algorithm. 
The experiment is launched as an HPO experiment, therefore, its configuration recognizes all parameters
in an HPO experiment (see :doc:`Configure HPO Algorithm <algorithm>` for parameter definitions). 
Some important parameters include:

+ **proposer**: HPO method used to propose new hyperparameter values 
+ **target**: "min" or "max", minimizing or maximizing user-defined HPO metric
+ **n_samples**: total number of jobs to run
+ **n_parallel**: number of parallel jobs

Another notable difference in automatic compression configuration is that for the values of the 
parameters in ``config_list``, a search space is defined via the following parameters:

+ **range**: [min, max] or a list of values
+ **type**:  `float`, `int`, `choice` types are supported

Additional parameters may be needed for specific Proposers (see 
:doc:`Configure HPO Algorithm <algorithm>`).

There are two potential scenarios for identifying the best hyperparameters. We will 
use hyperparameter "sparsity" as an example. In the first scenario, the user may set the same search range for the sparsity for
a group of layers defined in ``op_names`` or ``op_types``, however, the user allows the Proposer to choose a different value in the defined 
range for each layer in the group. While in the second scenario, the user would like to use the same sparsity value for 
all layers in the group due to the dependency among those layers.

To handle these two scenarios, we introduce an additional parameter ``expand_op_names`` ("true" or "false", default is "true"). 
If set to "true", Auptimizer will propose a different hyperparameter value for each layer defined in the group; whereas 
when set to "false", the same hyperparameter value will apply to all layers defined in the group.

For example, if the configuration is written as follows, in one job, the hyperparameter Proposer may assign sparsity value 0.2 and 0.4
to "conv1" and "conv2" layers, respectively.  However, if the ``expand_op_names`` is set to "false" in the following example, the Proposer
will always assign the same value (e.g., 0.2) to both "conv1" and "conv2" layers::

    [
        {
            'sparsity': {
                'range': [0.1, 0.9],
                'type': 'float'
            },
            'op_names': ['conv1', 'conv2'],
            'expand_op_names': true,
            'op_types': ['default']
        }
    ]

Step #3. Modify the training script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only a few modifications to the training script are needed to run a compression experiment. The  
modifications are the same for both one-time and automatic compression experiments. We first present 
an example training script and then explain the changes below::
    
    #!/usr/bin/env python   #Step 1: add shebang line to make script executable

    import aup               #Step 2: import auptimizer package

    def main(config):        #Step 3a: the main function should take "config" as argument
        
        ... # code to generate model and load dataset ...
        
        #Step 4: create a compressor and call the compress method to compress the model
        compressor = aup.compression.create_compressor(model, config, optimizer=optimizer)
        model = compressor.compress()

        #Step 5 (optional): speed-up the model by removing zero weights
        model = compressor.apply_speedup(dummy_input=torch.randn(1, 1, 28, 28).to(device))
        
        ... code for model fine-tuning after compression ...

        #Step 6 (optional): export the compressed model and the mask
        compressor.export_model(
            model_path="model_compressed.pth",
            mask_path="model_mask.pth",
            speedup=True,
            folder_name=".")
        
        #Step 7: return the metric for HPO or any metric for one-time compression
        aup.print_result(validation_acc)

    # Step 3b: parse the configuration file and call the main function as follows
    if __name__ == '__main__': 
        config = aup.BasicConfig().load(sys.argv[1])
        main(config)


1. Add Shebang line ``#!/usr/bin/env python`` on top of the script and make the script executable 
   (``chmod u+x script.py``).

2. Import Auptimizer package by ``import aup``

3. Parse the configuration file using ``aup.BasicConfig.load(sys.argv[1])``.

4. Create the compressor and apply compression

   + this can happen before the optimizer is created: 
     ``compressor = aup.compression.create_compressor(model, config)``
    
   + or after the optimizer is defined: 
     ``compressor = aup.compression.create_compressor(model, config, optimizer=optimizer)``
      
   Note: any additional arguments specifically required by the compression algorithms must be 
   passed here.

   Apply compression by ``compressor.compress()``.

5. (Optional) Speed-up can be applied for pruned models: 
   ``model = compressor.apply_speedup(dummy_input=torch.randn(*input_shape).to(device))``
   This will modify the actual architecture of the model by removing zero parameters. 
   ``dummy_input`` should be a ``pytorch tensor`` that conforms 
   to the model input shape. We recommend fine-tuning the model after applying model speed-up 
   as pruning zero parameters may affect the accuracy of the model.
   
   Note: Not all pruners support speed-up, please refer to the **Model Speed-Up** section below for more detail.

6. (Optional) Export the model::

    compressor.export_model(
            model_path="model_compressed.pth",
            mask_path="model_mask.pth",
            speedup=True,
            folder_name=".")

   This saves the model to disk. Note that the speed-up is only applied if it has not been applied
   yet; otherwise, the model is saved as it is.

   + ``model_path``: the path where the compressed model will be saved
   + ``mask_path``: is a pruning-only argument, the path where the pruning mask will be saved.
   + ``speedup``: must be present and True if speed-up has been applied; can be True if speed-up has not
     been applied yet, and will apply speed-up before saving the model.
   + ``folder_name``: (optional) the directory relative to the working directory to save the model,
     the model and mask files will be saved to ``working_directory/folder_name/model(mask)_path``.
   + ``dummy_input``: (optional) a ``pytorch tensor`` that conforms to the model input 
     shape required only for applying speedup when speedup has not been applied yet. 

7. Return the final result or any intermediate result by using ``aup.print_result``:

   + For one-time compression, this result can be any metric the user would like to visualize on the dashboard
   + For automatic compression, this result should be the metric to use in HPO

A few compression algorithms require additional changes in training procedures. 
Please refer to :doc:`Supported Compression Algorithms <compressors>` section for specific requirements
of each compressor.


Step #4. Run experiment
~~~~~~~~~~~~~~~~~~~~~~~

A one-shot compression experiment is run by issuing the ``aup.compression`` 
command::

    python -m aup.compression experiment.json

Automatic compression experiments require the ``--automatic`` flag::

    python -m aup.compression experiment.json --automatic


Advanced usages
---------------
Use decorator to modify training script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An alternative way to pass the configuration file to the training script is to use the decorator 
``aup_args`` with the following changes::

    @aup.aup_args
    def main(compression_type, compression_framework, compressor, config_list, folder_name = None, save_model = False):
        config = locals()
        ...

    if __name__ == '__main__':
        main(sys.argv[1])

Save the best model
~~~~~~~~~~~~~~~~~~~
Automatic compression experiments can use the "save best model" feature in HPO. If this 
feature is enabled, only the compressed model and mask obtained using the best hyperparameter 
combination will be exported, instead of all the models and masks for every hyperparameter 
combinations explored.

To use this feature, please make sure to define the following in the configuration file::

        "resource_args": {
            "save_model": true
        }

There are two ways to modify the code for exporting only the best model and its mask:

+ In case the ``@aup_args`` decorator is used, then the compressor's export_model method
  can be registered as a model saving function::

    aup_save_model(
        compressor.export_model,
        model_path="model_compressed.pth",
        mask_path="model_mask.pth",
        speedup=False)

+ Alternatively, if the decorator is not used, apply the following code::

    if "save_model" in config and config["save_model"]:
        compressor.export_model(
            model_path="model_compressed.pth",
            mask_path="model_mask.pth",
            speedup=False,
            folder_name=config["folder_name"])


Model Speed-up
--------------

NNI compression provides a `model speedup module <https://nni.readthedocs.io/en/stable/Compression/ModelSpeedup.html>`__ 
which aims to export models with their architecture modified to reflect 
the effect of pruning methods. Normally, users would export the model with its 
structure unchanged and, for pruning, a mask of the pruned weights. However, with 
model speed-up, the mask is applied to the model before exporting. 

**Important:** Note that without applying model speed-up, compression will not result in model size reduction or inference acceleration.

In order to use model speed-up, the script should call ``compressor.apply_speedup`` 
with the appropriate parameters. Model speed-up can also be used 
during ``compressor.export_model``. Please see `Modify the Training Script` step above for detailed usages.

Not all compression algorithms support model speed-up. Compressors that support model speed-up include:

+ ActivationAPoZRankFilter Pruner
+ ActivationMeanRankFilter Pruner
+ ADMM Pruner
+ FPGM Pruner
+ L1Filter Pruner
+ L2Filter Pruner
+ NetAdapt Pruner
+ Sensitivity Pruner
+ TaylorFOWeightFilter Pruner