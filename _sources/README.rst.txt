Auptimizer Quickstart
=====================

|GPL 3.0 License| |pipeline status| |coverage report| |repo url|

**Auptimizer** is an optimization tool for Machine Learning (ML) that automates many of the tedious parts of the model building and deployment process.
Currently, **Auptimizer** helps with:

-  **Getting the best models in minimum time** - Generate optimal models 
   and achieve better performance by employing state-of-the-art hyperparameter 
   optimization (HPO) techniques. Auptimizer will run and record sophisticated 
   HPO experiments on compute resources of your choice with effortless consistency 
   and reproducibility.

-  **Making your models edge-ready** - Get model-device compatibility and 
   enhanced on-device performance by converting models into the industry-standard 
   ONNX and TensorFlow Lite formats. Auptimizer-Converter provides validated 
   conversion techniques to ensure worry-free format transformations.

-  **Selecting the most suitable model for your edge deployment effortlessly** 
   - Compare how different models will perform under specific compute and memory 
   constraints on a CPU-based edge device. Auptimizer-Profiler will help you identify 
   the most efficient models without the hustle of going through multiple physical 
   deployment cycles.

Best of all, **Auptimizer** offers a consistent interface that allows
users to switch between different HPO algorithms conversion frameworks, 
and computing resources with minimal changes to their existing code.

In the future, **Auptimizer** will support end-to-end model building 
for edge devices, including model compression and neural architecture search. 

Capabilities
------------
Hyperparameter Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Auptimizer automates tedious experimentation by performing and recording 
hyperparameter experiments. Auptimizer provides a single seamless access 
point to top-notch HPO algorithms, including Bayesian optimization and multi-armed 
bandit. You can even integrate your own proprietary solution. Moreover, with 
Auptimizer, you can make the best use of your compute-resources. Whether you are 
using a couple of GPUs or AWS, Auptimizer will help you orchestrate compute resources 
for faster hyperparameter tuning. 

The table below shows a full list of currently supported techniques and resources 
for hyperparameter optimization.

+----------------------------------------------------------------+-----------------------------------+
| Supported HPO Algorithms                                       | Supported Infrastructure          |
+================================================================+===================================+
| | Random                                                       | | Multiple CPUs                   |
| | Grid                                                         | | Multiple GPUs                   |
| | `Hyperband <https://github.com/zygmuntz/hyperband>`__        | | Multiple Machines (SSH)         |
| | `Hyperopt <https://github.com/hyperopt/hyperopt>`__          | | EC2 instances                   |
| | `Spearmint <https://github.com/JasperSnoek/spearmint>`__     |                                   |
| | `BOHB <https://github.com/automl/HpBandSter>`__              |                                   |
| | `EAS (experimental) <https://github.com/han-cai/EAS>`__      |                                   |
| | Passive                                                      |                                   |
+----------------------------------------------------------------+-----------------------------------+

Profiler
~~~~~~~~
`Profiler <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/src/aup/profiler>`__ 
is a simulator for profiling performance of machine learning model scripts. Given compute- and memory 
resource constraints for a CPU-based Edge device, Profiler can provide estimates of compute and memory 
usage for model scripts on the device. These estimations can be used to choose best performing models or, 
in certain cases, to predict how much compute and memory models will use on the target device. 

Because Profiler mimics the target device environment on the user's development machine, the user 
can gain insights about the performance and resource needs of a model script without having to 
deploy it on the target device. Profiler helps accelerate the model selection cycle and simplifies 
finding model-device fit. Please see :doc:`prof_readme` for usages.

Converter
~~~~~~~~~
`Converter <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/src/aup/dlconvert>`__ 
is a format conversion tool for machine learning models. It encapsulates best practices of individual 
machine learning model conversions under a single API. Converter makes ML models suitable for edge 
(on-device) deployments by transforming them into the industry-standard ONNX and TensorFlow Lite formats 
and reducing model size through quantization. Please see :doc:`dlconvert_readme` for usages.

Install
-------

**Auptimizer** currently is well tested on Linux systems, it may require
some tweaks for Windows users.

::

   pip install auptimizer

**Note** Dependencies are not included. Using ``pip install -r``
`requirements.txt <https://github.com/LGE-ARC-AdvancedAI/auptimizer/blob/master/requirements.txt>`_ will install
necessary libraries for all functionalities.

Example
-------

::

   cd Examples/demo
   # Setup environment (Interactively create the environment file based on user input)
   python -m aup.setup
   # Setup experiment
   python -m aup.init
   # Create training script - auto.py
   python -m aup.convert origin.py experiment.json demo_func
   # Run aup for this experiment
   python -m aup experiment.json

Each job’s hyperparameter configuration is saved separately under
``jobs/*.json`` and is also recorded in the SQLite file
``.aup/sqlite3.db``.

.. figure:: ./images/demo.gif
   :alt: demo

License
-------

`GPL 3.0 License <./LICENSE>`__

.. |GPL 3.0 License| image:: https://img.shields.io/badge/License-GPL%203.0-blue.svg
    :target: https://opensource.org/licenses/GPL-3.0
.. |pipeline status| image:: https://travis-ci.org/LGE-ARC-AdvancedAI/auptimizer.svg?branch=master
   :target: https://travis-ci.org/LGE-ARC-AdvancedAI/auptimizer
.. |coverage report| image:: https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer
.. |repo url| image:: https://img.shields.io/badge/github-repo-information.svg
    :target: https://github.com/LGE-ARC-AdvancedAI/auptimizer


Cite
----

If you have used this software for research, please cite the following paper (accepted at IEEE Big Data 2019):

.. code-block:: none

   @misc{liu2019auptimizer,
    title={Auptimizer -- an Extensible, Open-Source Framework for Hyperparameter Tuning},
    author={Jiayi Liu and Samarth Tripathi and Unmesh Kurup and Mohak Shah},
    year={2019},
    eprint={1911.02522},
    archivePrefix={arXiv},
    primaryClass={cs.LG}
   }