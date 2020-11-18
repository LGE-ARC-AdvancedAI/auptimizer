"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

Convert to TF frozen ProtoBuf
=============================
"""
from typing import List
import logging
import tensorflow.compat.v1 as tf # pylint: disable=import-error

tf.disable_eager_execution()
logger = logging.getLogger(__name__) # pylint: disable=invalid-name


def to_frozen(sess: tf.Session, output_nodes: List[str], clear_devices: bool = True) -> tf.GraphDef:
    """Convert to TF frozen ProtoBuf based on current TF session.  
    See `reference <https://stackoverflow.com/questions/45466020/how-to-export-keras-h5-to-tensorflow-pb>`_.

    Args:
        sess (tf.Session): TF session contains the compute graph
        output_nodes (List[str]): list of output node names
        clear_devices (bool, optional): to clear device placement. Defaults to True.

    Returns:
        tf.GraphDef: frozen GraphDef to write to ProtoBuf
    """
    graph = sess.graph
    for i, output_node in enumerate(output_nodes):
        if ":" in output_node:
            logger.info("remove ':x' from tensor name %s", output_node)
            output_nodes[i] = output_node.split(":")[0]
    input_graph_def = graph.as_graph_def()
    if clear_devices:
        for node in input_graph_def.node:
            node.device = ''
    try:
        frozen_graph = tf.graph_util.convert_variables_to_constants(
            sess, input_graph_def, output_nodes)
    except AssertionError as error:
        logger.fatal('find mis-match graph')
        raise error
    return frozen_graph
