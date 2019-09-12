"""
Demonstration code for Rosenbrock function
==========================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: BSD-3-Clause

"""


def rosenbrock(x, y, a=1, b=100):
    return (a-x)*(a-x) + b*(y-x*x)*(y-x*x)

