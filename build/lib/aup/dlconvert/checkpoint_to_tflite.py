#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Checkpoint to TFLite
====================

Require checkpoint folder with `.meta` file.  Otherwise, please save the meta file manually before convertion.

Example
-------

.. code-block:: bash

   $ python -m aup.dlconvert.checkpoint_to_tflite.py --model  model_ckpt/ckpt.meta \\
       --output model_tflite.tflite \\
       --input_nodes input:0 \\
       --output_nodes output/Softmax:0 \\
       [--input_shape 1,224,224,3]

"""
from os import path, remove
from typing import List
import tensorflow.compat.v1 as tf # pylint: disable=import-error
from absl import flags, app
from .utils import reset_flag
import logging
logger = logging.getLogger("aup.dlconvert")

FLAGS = flags.FLAGS
reset_flag()

# pylint: disable=wrong-import-position
from .to_frozen_pb import to_frozen
from .pb_to_tflite import model_loader
from .to_tflite import create_converter

def convert(checkpoint_meta_file: str, output_nodes: List[str] = ()):
    """Convert TF Checkpoint to TFLite model

    Args:
        checkpoint_meta_file (str): checkpoint meta file name
        output_nodes (List[str], optional): A list of output node names for frozen graph. Defaults to ().

    Returns:
        tflite model 

    """
    model_dir = path.dirname(checkpoint_meta_file)
    ckpt = tf.train.get_checkpoint_state(model_dir)
    # check if valid checkpoint file can be loaded
    if ckpt is None:
        return None
    # convert to frozen graph first
    g = tf.Graph()
    with g.as_default():
        saver = tf.train.import_meta_graph(ckpt.model_checkpoint_path+".meta",
                                           clear_devices=True)
        graph_def = g.as_graph_def()
    with tf.Session(graph=g) as sess:
        saver.restore(sess, ckpt.model_checkpoint_path)
        graph_def = to_frozen(sess, output_nodes)  
    
    with open("tmp.pb", "wb") as fp: 
        fp.write(graph_def.SerializeToString())  
    # convert from froze protobuf to tflite
    converter = create_converter("tmp.pb", model_loader)
    tflite_model = converter.convert()
    
    remove("tmp.pb")
    return tflite_model

def _main(_):
    tflite_model = convert(FLAGS.model, FLAGS.output_nodes.split(","))
    try:
        with open(FLAGS.output, "wb") as f:
            f.write(tflite_model)
    except Exception as e:
        logging.fatal("No valid checkpoint file found")
        raise e

if __name__ == "__main__":
    app.run(_main)
