# Model Conversion Examples

This folder contains examples that demonstrate Converter coverage and efficacy.

### - Evaluating supported model architectures 
[Tested_Models](/Examples/converter_examples/Tested_Models) - This example evaluates common model architecture coverage by the individual conversion functions. It also summarizes known issues. **We strongly recommend that users review this example first before running their conversion tasks.**

### - Benchmarking quantized TensorFlow Lite models on an Android phone
[Convert_Benchmark](/Examples/converter_examples/Convert_Benchmark) - This example demonstrates how to benchmark quantized TensorFlow Lite model performance (i.e. running time and memory usage) on an Android phone. Specifically, we converted models from a TensorFlow frozen protobuf file to a quantized .tflite file, and benchmarked their performance on an LG G6 mobile phone. 

This example shows that models converted and quantized with Converter match the performance of the official quantized
models provided in the [TensorFlow repo](https://github.com/tensorflow/models/blob/master/research/slim/nets/mobilenet_v1.md).

### - Profiling performances of converted models using Auptimizer Profiler
[Convert_Profiler](/Examples/converter_examples/Convert_Profiler) - This example demonstrates how to use Auptimizer-Profiler to profile TensorFlow or ONNX model performance on CPU. Performance benchmarking scripts are provided for TensorFlow and ONNX. 

### How to run the examples

If you have not done so, please install the packages in `dlconvert_requirements.txt` before running the examples included in this directory.

```bash
pip install -r dlconvert_requirements.txt
```

We provide specific instructions for each example in the respective folder.


