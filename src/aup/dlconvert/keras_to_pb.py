#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Keras to ProtoBuf
=================

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.keras_to_pb.py --model model.h5 \\
       --output model.pb \\
       --frozen \\
       --output_nodes output/Softmax:0

"""
from os import path
from typing import List
from absl import flags, app
import tensorflow as tf
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag()
from .to_frozen_pb import to_frozen # pylint: disable=wrong-import-position

flags.DEFINE_string("model", "model.h5", "input model", short_name="i")
flags.DEFINE_string("output", "model.pb", "output", short_name="o")
flags.DEFINE_bool("frozen", True, "create frozen protobuf")
flags.DEFINE_string("output_nodes", "output/Softmax:0", "output nodes (separated by comma)")
flags.register_validator("model", path.isfile, message="missing input model")


def _to_graphdef():
    sess = tf.compat.v1.keras.backend.get_session()
    graph = sess.graph
    return graph.as_graph_def()


def convert(model: str, frozen: bool = False, output_nodes: List[str] = ()) -> tf.compat.v1.GraphDef:
    """Convert Keras model to tensorflow graphdef

    Args:
        model (str): Keras model file name
        frozen (bool, optional): To frozen graphdef. Defaults to False.
        output_nodes (List[str], optional): output nodes, otherwise, use model outputs from Keras model. Defaults to ().

    Returns:
        tf.GraphDef: Tensorflow GraphDef
    """
    model = tf.keras.models.load_model(model)
    tf.compat.v1.keras.backend.set_learning_phase(0)
    if frozen:
        if not output_nodes:
            output_nodes = model.output.op.name
        sess = tf.compat.v1.keras.backend.get_session()
        protobuf = to_frozen(sess, output_nodes)
    else:
        protobuf = _to_graphdef()
    return protobuf


def _main(_):
    protobuf = convert(FLAGS.model, FLAGS.frozen, FLAGS.output_nodes.split(","))
    with open(FLAGS.output, 'wb') as fp:
        fp.write(protobuf.SerializeToString())


if __name__ == "__main__":
    app.run(_main)
