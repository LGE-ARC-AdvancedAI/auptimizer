#!/bin/bash
#  Copyright (c) 2018 LG Electronics Inc.
#  SPDX-License-Identifier: GPL-3.0-or-later

set -e

cd tests/dlconvert/data

rm -rf test_model_ckpt test_savedmodel test_model.h5 test_model.pb

./create_test_model.py

python3 -m aup.dlconvert.keras_to_pb -i test_model.h5 -o test_model.pb --frozen --output_nodes output/Softmax
python3 -m aup.dlconvert.keras_to_onnx -i test_model.h5 -o test_model.onnx

cd ../../..