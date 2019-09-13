Examples
========

An easy way to get started with **Auptimizer** is to modify the demo code in the ``Examples`` folder.

+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| Example                                 | Folder                  | Purpose                                                                       |
+=========================================+=========================+===============================================================================+
| Basic Demo                              | ``demo``                | Tutorial                                                                      |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `2D function with different HPOs`       | ``2dfunc_diff_opt``     | Show how to switch between different optimizers                               |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `2D function with different resources`  | ``2dfunc_diff_res``     | Show how to switch between different resources                                |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `MNIST DNN`                             | ``hpo_mnist``           | Show HPO usage for DNN                                                        |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `Tensorflow flags`                      | ``tf_flags``            | Show how to integrate with Tensorflow Flags                                   |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `Tensorflow Iris`                       | ``tf_iris_diff_opt``    | Show example on Iris data                                                     |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `NAS integration`                       | ``cai_nas``             | Show how to do NAS (uses a publicly available open-source NAS implementation) |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
| `Failure Control`                       | ``job_failure_control`` | Show job failure control cases                                                |
+-----------------------------------------+-------------------------+-------------------------------------------------------------------------------+
 

Auto convert
~~~~~~~~~~~~

The ``experiment_auto.json`` shows how experiment configuration is managed.
The user can use::

  python -m aup.convert rosenbrock_origin.py experiment_auto.json rosenbrock

to automatically convert the original file to the **Auptimizer** version.
The output file name is defined in ``experiment_auto.json`` as ``script``.

Manual modification
~~~~~~~~~~~~~~~~~~~

We also provide a modified version for users' reference. In ``rosenbrock_hpo.py``, we show how to convert the function for tuning with **Auptimizer**.

For the end-user’s experiment, simply replacing the ``rosenbrock()`` function with their code is enough to use **Auptimizer** (**Need to return the score in that function**).

Experiment configurations
~~~~~~~~~~~~~~~~~~~~~~~~~

Different ``experiment*.json`` files illustrate how to specify the configuration for different HPO algorithms. Most of
them are identical. To set up a new experiment, please define the corresponding ``parameter_config`` in the ``JSON``
file.
