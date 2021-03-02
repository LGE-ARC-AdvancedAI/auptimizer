Configure HPO Algorithm
=======================

Supported algorithms
--------------------

**Auptimizer** supports a number of different HPO algorithms.  The names and descriptions are listed below:

===========  ============================================================================================================================
Name         Algorithm
===========  ============================================================================================================================
passive      Manually run job (for debug purpose)
random       Random search
sequence     Grid Search
spearmint    `Spearmint <https://github.com/JasperSnoek/spearmint>`_: Bayesian Optimization based on Gaussian Process
bohb         `HpBandSter <https://automl.github.io/HpBandSter/build/html/index.html>`_: Bayesian Optimization and HyperBand
hyperopt     `Hyperopt <http://hyperopt.github.io/hyperopt/>`_: Bayesian Optimization with Tree of Parzen Estimators (TPE)
hyperband    `Hyperband <https://github.com/zygmuntz/hyperband>`_: Multi-armed bandit approach
eas          `EAS <https://github.com/han-cai/EAS>`_: Efficient Architecture Search by Network Transformation (Illustration purpose)
===========  ============================================================================================================================


Use ``python -m aup.init`` to set up the experiment configuration interactively.

For finer control, advanced users can change the configuration manually by directly modifying the ``experiment.json``
file.

Configuration details
---------------------

Below we cover the most common pieces. For requirements related to specific algorithms, please refer to the respective
documentation.

The general structure of the configuration file is as follows::

 {
  "proposer": "random",
  "n_samples": 10,
  "random_seed": 1,
  "script": "auto.py",
  "parameter_config": [
    {
      "name": "x",
      "range": [
        -5,
        5
      ],
      "type": "float"
    }
  ],
  "resource": "cpu",
  "resource_args": {
    "save_model": true
  },
  "job_failure": {
    "job_retries": 3,
    "ignore_fail": true
  },
  "n_parallel": 3,
  "target":"min",
  "workingdir:"./"
 }


================ ======== ==============================================================================
Name             Default  Explanation
================ ======== ==============================================================================
proposer         random   hpo method used to propose new hyperparameter values (see below for full list)
n_samples        10       number of jobs to run
script           -        script to run
n_parallel       1        number of parallel jobs
job_retries      0        number of retries for failed jobs. 
ignore_fail      False    whether to continue the experiment if a job fails. 
target           max      search for max or min
resource         -        type of resource to run the experiment, [cpu, gpu, aws, node, passive]
parameter_config {}       hyperparameter specification (see below)
workingdir       "./"     path to run the script, important for running jobs remotely (SSH/AWS)
resource_args    {}       other parameters to enable features like tracking intermediate results, saving best model, etc (see below)
================ ======== ==============================================================================

for ``parameter_config``:

================= ======================================================================================
Name              Content                                                                               
================= ======================================================================================
name              name of the hyperparameter variable. Must be the same as used in the training script
range             [min, max] or a list of values                                                   
type              `float`, `int`, `choice` types are supported                                     
================= ======================================================================================

Minor modifications or changes may be required for each algorithm. These options can be found at the corresponding API
pages under :doc:`aup.Proposer` (see API links below).

for ``resource_args``:

========================== ======== ==============================================================================
Name                       Default  Explanation
========================== ======== ==============================================================================
save_model                 False    whether to save the best performing model (see below)
multi_res_labels           None     a list of additional results to be tracked, e.g. ["flops", "param"]
track_intermediate_results False    if true, intermediate results during training epoches will be tracked
early_stop                 None     parameters related to early stopping strategies
========================== ======== ==============================================================================

For details of the ``early_stop`` parameter and how to apply early stopping strategies to HPO experiments, please refer to 
:doc:`Early Stopping <early_stop>`. 

``resource_args`` can also include SSH/AWS specific parameters, please refer to :ref:`AWSRuntimeAnchor` for more details.

**Note**: 

| If ``job_failure`` is not specified, the experiment will stop whenever a job fails.
| For ``job_retries``, preferance is given to a different resource, if multiple resources are available.
| For ``ignore_fail``, currently [BOHB, EAS, Hyperband] proposers do not support experiment continuation upon job failure.

Additional functionalities
--------------------------
Track intermediate results
~~~~~~~~~~~~~~~~~~~~~~~~~~

This feature allows the user to save and track multiple intermediate results at different points during the HPO experiment. Auptimizer still uses the final result as the main result for the HPO algorithm, but saves the intermediate records in the database under the table ``intermediate_results``.


Usage
@@@@@

The feature can be used by adding the following parameter to the experiment configuration file::


  "resource_args": {
    "track_intermediate_results": true
   }

Then in the training script, ``aup.print_result(res)`` should be placed where the user wants the results to be tracked::

  def main(*args, **kwargs):
      # model and data preparation
      for epoch in range(n_epochs):
          # training for one epoch
          aup.print_result(res)

In the above example, the intermediate results are returned every epoch. The result at last epoch is regarded as the main result for the user script and is then used by the HPO algorithm.

The intermediate results will be shown on the dashboard if tracked.

**Note**: It is possible to use multiple results feature in conjunction with intermediate results to track multiple intermediate results as well.



Save the best model
~~~~~~~~~~~~~~~~~~~
This feature allows the user to save the best performing model after running the HPO experiment. This is achieved by
running the training script again using the best hyperparamters obtained during HPO the experiment. 
The model, by default, will be saved to path ``aup_models/models_<eid>/<user_defined_model_path>``. 

Usage
@@@@@

In order to use this feature, please add the following parameter to the experiment configuration file::

  "resource_args": {
    "save_model": true
   }

Depending on whether the ``@aup_args`` decorator is used, the training script needs the following additional modifications.

If ``@aup_args`` is used, the user needs to define a funtion to save the model, and register this function with ``aup_save_model``. 
We suggest using this approach if running the experiment on remote machines (SSH/AWS) to be able to correctly locate and retrieve the model saved 
on the remote machine. 

Please see the example below::

  # define a function "save_model(model)" to save the model to a user-defined path
  def save_model(model):
      os.makedirs('model_train')
      model.save('./model_train/mnist.h5')
  
  @aup_args
  def main(*args, **kwargs):
      # training code
      ...
      # register the model saving function with model as argument
      aup.aup_save_model(save_model, model)

      ...

If ``@aup_args`` is not used, the user needs to manually check whether the ``save_model`` parameter is True in the job's 
configuration. The main function should also take ``save_model`` and ``folder_name`` as arguments. Please see the 
example below::

  def main(*args, **kwargs, save_model=False, folder_name=None):
      # training code
      ...
      if save_model is True:
          # manually locate the path for saving the model
          # this is important if running on remote machines
          path = os.path.join('aup_models', folder_name)

          if os.path.exists('aup_models') is False:
              os.makedirs('aup_models')

          if os.path.exists(path) is True:
              shutil.rmtree(path)

          os.makedirs(path)
          os.chdir(path)

          model.save('./model_train/mnist.h5')
      ...

Return multiple results
~~~~~~~~~~~~~~~~~~~~~~~


This feature allows the user to save and track multiple secondary results along with the primary result for the HPO experiment. Auptimizer still uses the main result for the HPO algorithm, but saves the secondary results in the database under the table ``multiple_results``. There is no upper limit 
on how many secondary results the user can track.


Usage 
@@@@@


The feature can be used by adding the following parameter to the experiment configuration file::

  "resource_args": {
    "multi_res_labels": ["x", "y"]
  }

In the above configuration file, ``x`` and ``y`` are the secondary results the user wants to track and record. The user script would then return the results as a list including the primary result ``res`` along with the secondary parameters as follows::

  @aup_args
  def HPO():
    res = calculate_results()
    return [res, x, y]

In the above example, ``res`` is the primary result which is always placed at the first index of the returned list, which will be used by the HPO algorithm. The remaining results are matched directly with the list provided in ``multi_res_labels``. Hence, the length of the returned list from user script is  1 + length of ``multi_res_labels`` parameter.

**Note**: It is possible to use multiple results feature in conjunction with intermediate results to track multiple intermediate results as well.



Pause and resume jobs
~~~~~~~~~~~~~~~~~~~~~
+ Serial: optimize parameters by running jobs sequentially
+ Parallel: optimize parameters by running jobs in parallel
+ Pause: pause and save current HPO status
+ Resume: resume previously paused HPO process

+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Algorithm | Documentation                                   | Serial | Parallel | Pause (save) | Resume |
+===========+=================================================+========+==========+==============+========+
| Random    | :class:`aup.Proposer.RandomProposer`            | |Y|    | |Y|      | |Y|          | |Y|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Sequence  | :class:`aup.Proposer.SequenceProposer`          | |Y|    | |Y|      | |Y|          | |Y|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Passive   | :class:`aup.EE.Resource.PassiveResourceManager` | |Y|    | |Y|      | |Y|          | |Y|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Spearmint | :class:`aup.Proposer.SpearmintProposer`         | |Y|    | |Y|      | |N|          | |N|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Hyperopt  | :class:`aup.Proposer.HyperoptProposer`          | |Y|    | |Y|      | |N|          | |N|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| Hyperband | :class:`aup.Proposer.HyperbandProposer`         | |Y|    | |Y|      | |N|          | |N|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| BOHB      | :class:`aup.Proposer.BOHBProposer`              | |Y|    | |Y|      | |N|          | |N|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+
| EAS       | :class:`aup.Proposer.EASProposer`               | |Y|    | |N|      | |N|          | |N|    |
+-----------+-------------------------------------------------+--------+----------+--------------+--------+


.. |Y| unicode:: U+2713 .. checked
.. |N| unicode:: U+274C .. no check
.. |?| unicode:: U+274C .. check pending


