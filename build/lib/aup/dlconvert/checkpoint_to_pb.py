#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Checkpoint to TF ProtoBuf
=========================

Require checkpoint folder with `.meta` file.  Otherwise, please save the meta file manually before convertion.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.checkpoint_to_pb.py --model  model_ckpt/model.meta \\
       --output model_frozen.pb \\
       --frozen \\
       --output_nodes output/Softmax:0

"""
from os import path
from typing import List
import tensorflow.compat.v1 as tf # pylint: disable=import-error
from absl import flags, app
from .utils import reset_flag

FLAGS = flags.FLAGS
reset_flag()

# pylint: disable=wrong-import-position
from .to_frozen_pb import to_frozen

flags.DEFINE_string("model", "model-ckpt/model.meta", "input model ckpt meta file path", short_name="i")
flags.DEFINE_string("output", "model.pb", "output filename", short_name='o')
flags.DEFINE_bool("frozen", True, "create frozen protobuf")
flags.DEFINE_string("output_nodes", "", "model output names (separated by comma)")
flags.register_validator("model", path.isfile, message="Input checkpoint meta file is missing")
flags.register_validator("output_nodes", lambda x: len(x.split(','))>0, message="Provide at least one output node name")


def convert(checkpoint_meta_file: str, frozen: bool = False, output_nodes: List[str] = ()) -> tf.GraphDef:
    """Convert TF Checkpoint to ProtoBuf

    Args:
        checkpoint_meta_file (str): checkpoint meta file name
        frozen (bool, optional): to create a frozen graphdef. Defaults to False.
        output_nodes (List[str], optional): A list of output node names for frozen graph. Defaults to ().

    Returns:
        tf.GraphDef: Tensorflow Graph to be written to file

    """
    model_dir = path.dirname(checkpoint_meta_file)
    ckpt = tf.train.get_checkpoint_state(model_dir)
    g = tf.Graph()
    with g.as_default():
        saver = tf.train.import_meta_graph(ckpt.model_checkpoint_path+".meta",
                                           clear_devices=True)
        input_graph_def = g.as_graph_def()
    with tf.Session(graph=g) as sess:
        saver.restore(sess, ckpt.model_checkpoint_path)
        if frozen:
            input_graph_def = to_frozen(sess, output_nodes)    
    return input_graph_def


def _main(_):
    protobuf = convert(FLAGS.model, FLAGS.frozen, FLAGS.output_nodes.split(","))
    with open(FLAGS.output, "wb") as fp: # pylint: disable=invalid-name
        fp.write(protobuf.SerializeToString())


if __name__ == "__main__":
    app.run(_main)
