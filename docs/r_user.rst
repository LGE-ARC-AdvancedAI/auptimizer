Setup for R
===========

Install Auptimizer for R User
-----------------------------

.. code:: R

    install.packages('aup')

See below for setting up Auptimizer.

Experiment Setup
----------------

Auptimizer is running in Python.  See setup in Python first.

The main workflow is blow:

1. Setup Python Auptimizer environment by ``python -m aup.setup``
2. Change your R script:

   a. Make all hyperparameters as global variables.
   b. Add ``#!/usr/bin/env Rscript`` as the first line.
   c. Add ``source("auptimizer")``.
   d. Add ``get_config()``, which will automatically update the hyperparameters globally set in step a.
   e. Add ``print_result(score)`` to return the target score you want to optimize for you script.
   f. Change file permission as ``chmod u+x <your_R_script>``.
   g. Add them into an Auptimizer experiment by ``python -m aup.init``.

3. Run Auptimizer as ``python -m aup experiment.json``.

Examples
--------

We provide two simple examples to use auptimizer on `Github <https://github.com/LGE-ARC-AdvancedAI/auptimizer/R-src/example>`__.

More Information
----------------

See `Auptimizer Github <https://github.com/LGE-ARC-AdvancedAI/auptimizer>`__ for more information.