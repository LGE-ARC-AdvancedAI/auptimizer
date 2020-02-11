Create and run a new experiment
===============================

**Auptimizer** needs a modified training script and an experiment specification file before use.
There are three approaches:

+ `Manual conversion <#how-to-modify-existing-code-for-auptimizer>`_;
+ `Python decorator <#code-conversion-with-decorator>`_;
+ `Auto conversion for script (beta) <#auto-code-conversion>`_.


Terminology
-----------

For data science applications, the **user** (AI scientist/engineer) solves a given data mining problem with a specified
machine learning model.

A script (**code**) is written and some hyperparameters are identified to be explored during model training.

Typically, the user carries out an **experiment** to examine a range of hyperparameter combinations  and measures the
**performance** of the model on a hold-out dataset. For example, testing a deep learning model by exploring the learning
rate between 0 and 1, and dropout between 0.4 and 0.6. the performance is measured by accuracy.

Each individual training process for a given selection of hyperparameters (e.g., learning rate = 0.1, dropout = 0.5)  is
called a **job**.

All jobs run on an assigned computational **resource**, e.g. CPU, GPU. And after all jobs are finished, the user
retrieves the best model from the training history for further analysis or application.

How to modify existing code for Auptimizer
------------------------------------------

1. create the ``experiment.json`` file to specify the experiment and hyperparameters.  Using 

  .. code:: bash

    python -m aup.init

  will guide you interactively.  The structure is generally the same for most algorithms with minor modifications.  See
  :doc:`algorithm` for more details. 

2. To change your existing code, we have tools to convert as described in `Auto code conversion`_.  If you plan to change it manually, the general flow of the conversion process is as follows: 

  a. parse the configuration file (first argument from command line, i.e. ``sys.argv[1]``) using ``aup.BasicConfig.load(sys.argv[1])``.  And use the hyperparameters parsed from the ``BasicConfig`` in your code, such as ``config.param_name`` or ``config['param_name']``, where ``param_name`` need to be consistent with the one  used in ``experiment.json``.
  b. to report the result by using ``aup.print_result``.
  c. Add Shebang line ``#!/usr/bin/env python`` and make the script executable (``chmod u+x script.py``).

3. Your experiment is now ready to run via ``python -m aup experiment.json``. For more details, see `Run experiment`_. 

Code conversion with decorator
------------------------------

For better control, you can use `aup_args` or `aup_flags` to decorate your code.  The examples are in below:


.. figure:: images/comparison.png
   :alt: Code comparison

   Example of using decorator for code conversion.

Auto code conversion
--------------------

If your training function takes all hyperparameters as input, then  **Auptimizer** converts code to run if the training script is well defined as follows::

  python -m aup.convert <script> <exp_json> <func_name> -o [output]

* ``script`` the original script used for training, it must contain the function with name ``func_name``.  Also no "__main__" inside the script.
* ``exp_json`` experiment configuration defined by the user.  It must contain the hyperparameters used by ``func_name``.
* ``func_name`` the entry function used for training. It uses all hyperparameters defined in ``exp_json``. All other inputs need to be optional and not overlapping with the hyperparameter names.
* ``output`` optional name for output ``code``.  If not specified, it creates a file with the name specified in ``exp_json``.

Check out the folder ``Examples/2dfunc_diff_opt/README.md`` in the repository for example usage.

Run experiment
--------------

Once the experiment has been correctly set up, it is very easy to start the experiment::

  python -m aup experiment.json

Additional arguments
~~~~~~~~~~~~~~~~~~~~

+ ``--test``: will run in test mode by executing one job
+ ``--aup``: manually specify the ``.aup`` folder
+ ``--log``: set log level to ``[debug,info,warn,error]``
+ ``--sleep``: time delay for sequential jobs (avoid database collision)
+ ``--ignore_fail``: ignore failures in job execution

.. _AWSRuntimeAnchor:

Additional runtime configuration for node/AWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The user should either have Auptimizer installed on the remote machine, or at a minimum, copy the :download:`Auptimizer file for remote machine <archive/aup.py>` to the remote machine that can be imported by the jobs.

Additional configuration for node/AWS environment for runtime can be specified under the ``runtime_args`` in the ``experiment.json``.
This is important for setting up the environment, etc. on the remote machine.
The specific arguments are:

+ ``prescript``: any script to be run before the job. (use ; to separate different commands)
+ ``postscript``: any script to be run after the job.
+ ``overwrite``: remove the existing job file if exists.  Otherwise, it will use the existing file on the node.
+ ``env``: other environment variables, listed as dictionary `{"CUDA_VISIBLE_DEVICES":"0"}`

Other resource-related arguments are under `resource_args` (not for node resource):

+ ``retry``: number of 30s to wait if AWS instance has no response.  default is 10 (3 minutes).
+ ``shutdown``: turn off AWS instance after run.

See ``Examples/2dfunc_diff_res/`` for more references.


Results / further analysis
--------------------------

The output of an experiment is saved in two places: 

+ ``jobs/`` folder contains the configuration of each job in ``<job_id>.json`` and output of each job in ``<job_id>.out``.
+ ``.aup/sqlite.db`` database file contains the experiment history (configurations and results).  All jobs for different
  experiments are all saved under unique IDs, unless it has been reset.

