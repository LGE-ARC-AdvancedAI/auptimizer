"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
from google.protobuf import text_format
import tensorflow as tf
from typing import List

CONST_NAME=set(["Assign","Const","Shape"])

def load_graphdef(filename:str) -> tf.compat.v1.GraphDef:
    if "pbtxt" in filename:
        graph_def = text_format.Parse(open(filename, 'r').read(), tf.compat.v1.GraphDef())
    else:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(open(filename, 'rb').read()) 
    return graph_def


def verify_name(name: str, graphdef: tf.compat.v1.GraphDef) -> bool:
    """Verify the name is in graph
    
    Arguments:
        name {str} -- node name
        graphdef {tf.compat.v1.GraphDef} -- TF Graph definition
    
    Returns:
        bool -- Whether node name is in graph
    """
    for n in graphdef.node:
        if name == n.name:
            return True
    return False    


def search_input_names(graphdef: tf.compat.v1.GraphDef) -> List[str]:
    """Search for input nodes
    
    Arguments:
        graphdef {tf.compat.v1.GraphDef} -- TF Graph definition
    
    Returns:
        List[str] -- List of input node names
    """
    res = []
    for n in graphdef.node:
        if n.op == "Placeholder":
            res.append(n.name)
    return res


def search_output_names(graphdef: tf.compat.v1.GraphDef) -> List[str]:
    nodes = set(n.name for n in graphdef.node if n.name.split("/")[-1] not in CONST_NAME)
    for n in graphdef.node:
        for input_node in n.input:
            if input_node in nodes:
                nodes.remove(input_node)
    return list(nodes)