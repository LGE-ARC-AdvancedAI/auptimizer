# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

# R Package for Auptimizer

## Installation

*IMPORTANT:*  Auptimizer is well tested on Unix or similar OS.  Windows users may have to make some changes to run Aptimizer.

1. [Install Python Auptimizer](../README.md)
2. Install Auptimizer for R, (run R from `R-src` folder):

    ```R
    install.packages("devtools")
    devtools::install("Rpackage")
    ```

## Usage

The workflow for Auptimizer is the same as the Python version.  The difference is in how to change existing R code to use Auptimizer.

1. Setup Python Auptimizer environment using `python -m aup.setup`

2. Change your R script:

   a. Make all hyperparameters global variables.

   b. Add `#!/usr/bin/env Rscript` as the first line.

   c. Add `source("auptimizer")`.

   d. Add `get_config()`, which will automatically update the hyperparameters (set globally in step 2a).

   e. Add `print_result(score)` to return the target score you want to optimize for your script.

   f. Change file permission using `chmod u+x <your_R_script>`.

   g. Add them into an Auptimizer experiment using `python -m aup.init`.

3. Run Auptimizer using `python -m aup experiment.json`.

## Examples

See examples in [example].

+ `exp_ridge.R` for synthetic Ridge regression. Run as `python -m aup ridge.json`.
+ `exp_rosenbrock.R` for analytic Rosenbrock function. Run as `python -m aup rosenbrock.json`.
