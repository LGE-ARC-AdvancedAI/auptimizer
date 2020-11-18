#!/usr/bin/env python
"""Optmize ONNX for runtime

See [here](https://github.com/onnx/onnx/blob/master/docs/PythonAPIOverview.md#optimizing-an-onnx-model).


Problematic, and uncertain about the future. https://github.com/onnx/onnx/issues/2417
"""

import onnx
from onnx import optimizer
from absl import flags, app
from os import path
from .utils import reset_flag
FLAGS = flags.FLAGS
reset_flag()
flags.DEFINE_string("model", "model.onnx", "input model", short_name="m")
flags.DEFINE_string("output", "model_opt.onnx", "output path", short_name="o")
flags.DEFINE_string("optimize", "default", "optimize pass names (sep by `,` or `all`)")
flags.register_validator("model", path.isfile, message="missing input model")

ALL_OPT = optimizer.get_available_passes()

def optimize(filename:str, output:str):
    model = onnx.load(filename)

    if FLAGS.optimize == "default":
        passes = None
    else:
        passes = FLAGS.optimize.split(",")
        assert all([p in ALL_OPT for p in passes])

    model = optimizer.optimize(model, passes)

def main(unused):
    optimize(FLAGS.model, FLAGS.output)


if __name__ == "__main__":
    app.run(main)
