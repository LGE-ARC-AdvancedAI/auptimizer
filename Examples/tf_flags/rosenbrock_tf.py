#!/usr/bin/env python
"""
Modified Rosenbrock function with tf.app.flags
==============================================

..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""

import sys
import tensorflow as tf

flags = tf.app.flags
FLAGS = flags.FLAGS

flags.DEFINE_float("x", 0, "x value")
flags.DEFINE_float("y", 0, "y value")


def rosenbrock(x, y, a=1, b=100):
    return (a-x)*(a-x) + b*(y-x*x)*(y-x*x)


def main(unused):
    val = rosenbrock(FLAGS.x, FLAGS.y)
    print(val)


if __name__ == "__main__":
    tf.app.run()
