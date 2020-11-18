"""Optimize ProtoBuf graph

See [here](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms)

NO python script at the moment.


1. git clone tensorflow

2. bazel build tensorflow/tools/graph_transforms:transform_graph

3a. summarize_graph --in_graph=test_model.pb
3b. transform_graph --in_graph=test_model.pb --out_graph=opt_model.pb --inputs=input --outputs=output/Softmax --transforms='strip_unused_nodes(type=float, shape="1,224,224,3") fold_constants(ignore_errors=true)' && echo "success"
4. ../../conversion/pb_to_tflite.py --model opt_model.pb --output opt_model.tflite
"""

