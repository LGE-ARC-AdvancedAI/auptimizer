# R Package for Auptimizer

## Installation

*IMPORTANT:*  Auptimizer is well tested on Unix or similar OS.  For windows users, some changes are required by themself.

1. [Install Python Auptimizer](../README.md)
2. Install Auptimizer for R, (run R from `R-src` folder):

    ```R
    install.packages("devtools")
    devtools:install("Rpackage")
    ```

## Usage

The workflow for Auptimizer is the same as the Python version.  The difference is how to change the existing R code.

1. Setup Python Auptimizer environment by `python -m aup.setup`
2. Change your R script:
   a. Make all hyperparameters as global variables.
   b. Add `#!/usr/bin/env Rscript` as the first line.
   c. Add `source("auptimizer")`.
   d. Add `get_config()`, which will automatically update the hyperparameters globally set in step a.
   e. Add `print_result(score)` to return the target score you want to optimize for you script.
   f. Change file permission as `chmod u+x <your_R_script>`.
   g. Add them into an Auptimizer experiment by `python -m aup.init`.
3. Run Auptimizer as `python -m aup experiment.json`.

## Examples

See examples in [example].

+ `exp_ridge.R` for synthetic Ridge regression. Run as `python -m aup ridge.json`.
+ `exp_rosenbrock.R` for analytic Rosenbrock function. Run as `python -m aup rosenbrock.json`.
