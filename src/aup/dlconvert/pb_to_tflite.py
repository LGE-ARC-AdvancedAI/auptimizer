#!/usr/bin/env python
"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

ProtoBuf to TFlite
==================

See :func:`dlconvert.to_tflite.setup_converter` for more control arguments for `tflite`.

Example
-------

.. code-block:: bash

    $ python -m aup.dlconvert.pb_to_tflite \\
        --model model.pb --output model.tflite \\
        [--load rep_data] \\
        [--opt default --ops int8 --type int8]
        [--input_shape 1,224,224,3]

"""
from os import path
import logging
from typing import List
from absl import flags, app
from tensorflow import lite, keras
import tensorflow as tf
from .utils import reset_flag

reset_flag()

# pylint: disable=wrong-import-position
from .to_tflite import create_converter
from .spec_utils import pb

logger = logging.getLogger(__name__) # pylint: disable=invalid-name

tf.compat.v1.disable_eager_execution()

flags.DEFINE_string("model", "model.pb", "input model", short_name="i")
flags.DEFINE_string("output", "model.tflite", "output", short_name="o")
flags.DEFINE_string("input_nodes", "input:0", "input tensor names")
flags.DEFINE_string("output_nodes", "output/Softmax:0", "output tensor names")
flags.DEFINE_string("input_shape", None, "input shape")
flags.register_validator("model", path.isfile, message="missing input model")
FLAGS = flags.FLAGS

def verify_input_names(input_names, graph_def):
    """Check if input_names are correct
    """
    graph_nodes = set(pb.search_input_names(graph_def))
    input_names = set(input_names)
    if graph_nodes != input_names:
        logger.fatal("Inconsistency in input nodes, graph has the following nodes:\n%s", "\n".join(graph_nodes))
        return False
    return True

def verify_output_names(output_names, graph_def):
    """Check if output_names are correct
    """
    flag = False
    for n in output_names:
        if not pb.verify_name(n, graph_def):
            logger.fatal("%s is not found in graph", n)
            flag = True
    if flag:
        names = pb.search_output_names(graph_def)
        logger.fatal("Potential output names:\n%s", "\n".join(names))
        return False
    else:
        return True


def find_node_shape(tensor_name:str, graph_def:tf.compat.v1.GraphDef) -> List[int]:
    """Find node shape for the given tensor name
    
    Args:
        tensor_name (str): name of the tensor
        graph_def (tf.compat.v1.GraphDef): TF GraphDef
    
    Raises:
        ValueError: When node name is not in the graph
    
    Returns:
        List[int]: tensor shape, excluding first (batch) dimension
    """
    tensor_name = tensor_name.split(":")[0]  # if :x is given
    shape = None
    for n in graph_def.node:
        if tensor_name in n.name:
            shape = [i.size for i in n.attr['shape'].shape.dim]  
            break
    if shape is None:
        raise ValueError("No match node for %s"%tensor_name)
    return shape[1:]


def model_loader(filename: str) -> lite.TFLiteConverter:
    """Load TF ProtoBuf (for TF v1 and v2)
    
    Args:
        filename (str): ProtoBuf file name
    
    Returns:
        lite.TFLiteConverter: TFLite converter
    """
    input_names = FLAGS.input_nodes.split(",")
    output_names = FLAGS.output_nodes.split(",")

    # Overwrite default input_shape with user defined input_shape
    if FLAGS.input_shape is not None:
        shapes = []
        input_shapes = FLAGS.input_shape.split(";")
        for input_shape in input_shapes:
            shape = [int(x) for x in input_shape.split(",")]
            shapes.append(shape)

    if tf.__version__[0] == "2":  # pylint: disable=no-member
        # require frozen pb
        logger.info("Tensorflow version 2.x")
        g = tf.Graph()
        graph_def = pb.load_graphdef(filename)
        if verify_input_names([i.split(":")[0] for i in input_names], graph_def):
            logger.info("Correct input names")
        else:
            raise Exception("Wrong input nodes")
        if verify_output_names([i.split(":")[0] for i in output_names], graph_def):
            logger.info("Correct output names")
        else:
            raise Exception("Wrong output nodes")
        # get input shapes
        if not FLAGS.input_shape:
            shapes = [find_node_shape(name, graph_def) for name in input_names]
        else:
            shapes = [shape[1:] for shape in shapes]
            
        # import protobuf and create Keras model
        with g.as_default():
            inputs = {}
            for name, shape in zip(input_names, shapes):
                inputs[name] = keras.layers.Input(shape=shape, name="input")
            tf.import_graph_def(graph_def, name="", input_map=inputs)
            tf_outputs = [g.get_tensor_by_name(name) for name in output_names]
            model = keras.Model(inputs=inputs, outputs=tf_outputs)
        return lite.TFLiteConverter.from_keras_model(model)
    else:
        logger.info("Tensorflow version 1.x")
        input_names = [i.split(':')[0] for i in input_names]
        output_names = [i.split(':')[0] for i in output_names]
        try:
            tflite_model = lite.TFLiteConverter.from_frozen_graph(filename, input_names, output_names)
        except Exception as e:
            graph_def = pb.load_graphdef(filename)
            if verify_input_names(input_names, graph_def):
                logger.info("Correct input names")
            if verify_output_names(output_names, graph_def):
                logger.info("Correct output names")
            raise e
        return tflite_model


def _main(_):
    logger.setLevel(logging.INFO)
    converter = create_converter(FLAGS.model, model_loader)
    tflite_model = converter.convert()
    with open(FLAGS.output, "wb") as f:
        f.write(tflite_model)

if __name__ == "__main__":
    app.run(_main)
