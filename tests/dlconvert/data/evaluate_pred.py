from absl import flags, app

import numpy as np
from os import path
import hashlib

flags.DEFINE_string("model", "test_model.tflite", 'model path')
flags.DEFINE_integer("seed", "123", "random seed")
FLAGS = flags.FLAGS


def run_lite():
    import tflite_runtime.interpreter as tflite
    intp = tflite.Interpreter(FLAGS.model)
    intp.allocate_tensors()
    input_idx = intp.get_input_details()[0]['index']
    intp.set_tensor(input_idx, np.random.random(size=(1,224,224,3)).astype(np.float32))
    intp.invoke()
    output_idx = intp.get_output_details()[0]['index']
    y = intp.get_tensor(output_idx)
    res = ",".join("%.5f"%i for i in y[0])
    print(res)
    print(hashlib.sha256(res.encode()).hexdigest()[:5])
    

def run_onnx():
    pass

def main(unused):
    np.random.seed(FLAGS.seed)
    if 'lite' in FLAGS.model.split(".")[-1]:
        run_lite()
    else:
        run_onnx()


if __name__ == "__main__":
    app.run(main)