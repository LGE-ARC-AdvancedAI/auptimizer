#!/usr/bin/env Rscript
# Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Example code to use Auptimzier.
library("auptimizer")
source("rosenbrock.R")

# Hyperparameters
x <- 10
y <- 20

get_config()
score <- rosen(c(x, y))
print_result(score)
