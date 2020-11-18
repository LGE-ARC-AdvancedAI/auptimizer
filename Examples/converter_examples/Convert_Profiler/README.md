# Profiling TensorFlow Lite/ONNX model performance for CPU
In this example, we show how to use Converter to convert models into edge device-friendly formats (TensorFlow Lite and ONNX) and then profile their performance (i.e. runtime and memory usage) on CPU using Auptimizer's Profiler package. 

We use standard image classification models in Protobuf format and convert them to TensorFlow or ONNX. Once we have models in a common format, we can benchmark their performance using Profiler with different hardware settings.

By pairing Auptimizer's Converter and Profiler capabilities, you can significantly reduce the effort needed to prepare an ML model for edge deployment. You can simply download models from various DL platforms and libraries, convert them to a common edge-friendly standard and estimate the script's runtime and memory usage for your target device constraints.


## How to run this example
- *Step 1*: Download a few protobuf models for testing 
  ``` 
  python download_test_models.py 
  ```
  and create a new folder called `output\_models`. 
The `download_test_models.py` script should download the squeezenet, densenet, and nasnet-mobile models into `input_models` directory.

- *Step 2*: Convert the models to TensorFlow Lite:

  ``` 
  python -m aup.dlconvert -f convert_tflite.json
  ```
- *Step 3*: Profile the converted TensorFlow Lite models and the downloaded official TensorFlow Lite models released by TensorFlow for the same model architecture. Run the following to do profiling:
  ```bash
  python -m aup.profiler -e env_tflite.template -f model_names_tflite.txt
  ```

  This creates an output text file with the details of the model performance. The Docker settings can be edited using the `env_tflite.template` file and the test script can be edited using `test_perf_tflite.py`.
  
We show output from running the example on MacOS. From `tflite_output.txt`, we see that the performances of the converted models are very close to those of the official TensorFlow Lite models, which validates that the conversion from Protobuf to TensorFlow Lite works correctly.

You can similarly convert the models to ONNX and profile the performances. The sample conversion configuration json file `convert_onnx.json` and the Profiling environment file `env_onnx.template` are provided.
