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
resource         -        type of resource to run the experiment, [cpu, gpu, passive, node]
parameter_config {}       hyperparameter specification (see below)
workingdir       "./"     path to run the script, important for running jobs remotely (SSH/AWS)
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

**Note**: 

| If ``job_failure`` is not specified, the experiment will stop whenever a job fails.
| For ``job_retries``, preferance is given to a different resource, if multiple resources are available.
| For ``ignore_fail``, currently [BOHB, EAS, Hyperband] proposers do not support experiment continuation upon job failure.

Additional functionalities
--------------------------

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


