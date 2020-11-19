# Converter

**Converter** is a format conversion tool for machine learning models. It encapsulates best practices of individual Machine Learning model conversions under a single API.

Converter allows you to:
- **Make your models edge device-friendly.** Transform models in Checkpoint (.meta), Keras (.h5/.hdf5), SavedModel (directory name), Protobuf (.pb), and Pytorch (.pt) into edge-optimized ONNX (.onnx) and TensorFlow Lite (.tflite) formats.
- **Enhance model interoperability through standardization.** Boost model compatibility with countless compilers, inference engines, and SoCs by converting it into the industry-standard ONNX format.
- **Get a smaller and faster model.** Make your model more compact and efficient by leveraging *[Quantization] (#sec-quantization)* built into the TensorFlow Lite converter.

The following source model formats (and file extensions) can be converted to **TensorFlow Lite (.tflite)** and **ONNX (.onnx)**:  
- **Checkpoint (.meta)**
- **Keras (.h5/.hdf5)**
- **SavedModel (directory name)**
- **Protobuf (.pb)**
- **PyTorch (.pt)**  

Additionally, Converter supports conversions:  
- from Checkpoint to Protobuf
- from Keras to Protobuf
- from PyTorch to Keras

TensorFlow 1.15, 2.1 - 2.3 and PyTorch 1.6.0 are tested. The conversion from SavedModel to TensorFlow Lite/ONNX requires TensorFlow version 2.x. Other conversions can be run using both TensorFlow 1.15 or 2.x. 

## Install

*Note:* Converter leverages conversion libraries that have different version requirements (mainly for TensorFlow).
It is highly recommended to use Docker or Python's virtualenv to isolate your environment. 

1. Install Auptimizer
2. If you would like to convert from Checkpoint/Keras/Protobuf/SavedModel model formats, please run:

```bash
pip install keras2onnx tf2onnx
``` 
If you would like to convert from PyTorch format, please run:

```bash
pip install pytorch2keras keras2onnx tf2onnx
```

## Usage

1. **Recommended:** Check whether your model architecture is supported for the target conversion [*here*](/Examples/converter_examples/Tested_Models).

2. **Important:** Ensure that you can load and run your model, otherwise you will not be able to convert it successfully.

3. Specify conversion parameters. There are certain parameters to specify for each type of conversion. These parameters need to be written in a configuration *.json* file. You can list configurations for multiple model conversion tasks in a single .json file to execute model conversions sequentially. An example configuration for converting a VGG16 Keras model to ONNX is as follows:
```bash
    {
        "convert_from":"test_models/VGG16.h5",
        "convert_to":"converted_models/VGG16_keras.onnx",
    }
```

4. After preparing the configuration .json file, run the following command to start the conversions.
```bash
    python -m aup.dlconvert -f <configuration json file> 
```
Alternatively, you can also write the configuration in a *json dictionary* format, and run
```bash
    python -m aup.dlconvert -d <configuration json dictionary> 
```


## Parameters

For **all** conversions, the two required parameters are **convert_from** and **convert_to**.

For each specific conversion, there can be additional parameters needed. These parameters are usually dependent on the source- and target model formats, and are summarized in the following chart:



|  From      | To      | quantization | input_nodes | output_nodes | network_script network_name |input_shape| onnx_opset | frozen| savedmodel_tag savedmodel_signature
| -----------| ------|-----------  |  -----------  | --------- | -----------  |  -----------  | --------- | ----------| ---------|
| Keras      |TensorFlow Lite | Optional |  
| SavedModel |TensorFlow Lite | Optional |   
| Checkpoint |TensorFlow Lite | Optional | Required |Required |  | Optional    
| Protobuf   |TensorFlow Lite | Optional |Required | Required | | Optional
| PyTorch    |TensorFlow Lite| Optional  | | |Required|Required
| Keras      |ONNX   |  | | | ||Optional | | |
| SavedModel |ONNX   |  | | | ||Optional | | Optional 
| Checkpoint |ONNX   |  |Required | Required | | Optional|Optional     
| Protobuf   |ONNX   |  |Required | Required | | Optional|Optional  
| PyTorch    |ONNX   |  | | | Required |Required| Optional| 
| Keras      |Protobuf|  | | Required| |||Optional| |
| Checkpoint |Protobuf|  | | Required| |||Optional| |
| PyTorch    |Keras  |  | | | Required | Required


**--convert_from**  
Required for **all** conversions. Input model file with one of the supported extensions: `.meta`, `.h5/.hdf5`, `.pb`, `.pt`, or a directory path for SavedModel.  

**--convert_to**  
Required for **all** conversions. Output model name with one of the supported extensions: `.tflite`, `.onnx`, `.pb`, or `.h5/.hdf5`.  

<a name="sec-quantization">
</a>

**--quantization**  
Parameter *quantization* includes a group of parameters used for enabling quantization while converting to TensorFlow Lite format. Post-training quantization is a built-in functionality of the TensorFlow Lite Converter. The Converter API supports calling this functionality.

To specify quantization parameters, write in the configuration .json file:
```bash
   {
        "convert_from":"test_models/VGG16.h5",
        "convert_to":"converted_models/VGG16_keras.tflite",
        "quantization": {
            "optimization":"default",
            "type":"float16",
            "opsset":"tf",
            "load":"repdata.py"
        }
    }
```

More detail on post-training quantization capabilities and parameter setting can be found in [Post-training quantization](https://www.tensorflow.org/lite/performance/post_training_integer_quant#convert_to_a_tensorflow_lite_model)

**--optimization**  
Enable/disable quantization for conversion. Choose from `none` or `default`. Default is `none`. When using `none`, no quantization will be performed and the converted TensorFlow Lite model will be in float32 format. When using `default`, best practices will be applied for quantization with the other given information via `--type`, `--opsset`, and `--load`.

**--type**  
Target data type for constant values of the converted TensorFlow Lite model. Choose from `float32`, `float16`, `int8`,and `uint8`. Default is `float32`. 

**--opsset**  
Set of OpsSet options supported by the target device (experimental). Choose from  
`tflite`, which refers to `[tensorflow.lite.OpsSet.TFLITE_BUILTINS]`,  
`tf`, which refers to `[tensorflow.lite.OpsSet.SELECT_TF_OPS, tensorflow.lite.OpsSet.TFLITE_BUILTINS]`,   
 and `int8`, which refers to `[tensorflow.lite.OpsSet.TFLITE_BUILTINS_INT8]`. Default is `tflite`. 

**--load**  
A python script that implements a data generation function that generates representative data for quantizing variable data, such as feature maps. The function should be named `get_dataset`, and it should be a generator function that yields large enough dataset to represent typical data values. Check [representative data](../../../Examples/converter_examples/Convert_Benchmark/repdata.py) for example.
 
**--input_nodes**  
Model input names (separated by comma), which can be found with [summarize graph tool](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms#inspecting-graphs). Those names typically end with `:0`, for example `input:0`.

**--output_nodes**  
Model output names (separated by comma). which can be found with [summarize graph tool](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms#inspecting-graphs). Those names typically end with `:0`, for example `output/Softmax:0`.

**--input_shape**  
If the `input_nodes` in *protobuf* or *checkpoint* has unspecified shapes other than the 1st dimension, the `input_shape` needs to be specified by a comma separated string, for example `1,3,224,224`. For multiple `input_nodes`, use `;` to separate their corresponding `input_shape`.  
The shape of `input_nodes` can also be checked using the [summarize graph tool](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms#inspecting-graphs), where unspecified shape is usually represented by **-1**. 

**--network_script**  
Path to a Python script that contains the model definition of the PyTorch model to be converted.

**--network_name**  
Class name of the model to be converted, defined in the script specified in `network_script` .

**--onnx_opset**  
Opset version to use for ONNX. Default is `10`. The ONNX opset version updates can be found in [ONNX release notes](https://github.com/onnx/onnx/releases).

**--frozen**  
Flag to control whether to create a frozen Protobuf. Default is `True`.  

**--savedmodel_tag**  
Tag to use for SavedModel. Default is `serve`. The SavedModel to be converted *cannot have an emtpy tag*.

**--savedmodel_signature**  
Signature to use for SavedModel within the specified `--tag` value. Default is `serving_default`. The SavedModel to be converted *cannot have an emtpy signature*.

**--skip**
This parameter is for converting selected models when there are multiple conversion configurations in the json file. When set to `True`, the model will be skipped and not be converted. Default is `False`. 


## Examples
We provide extensive examples on using model conversion in various use cases in [converter_examples](../../../Examples/converter_examples), including:

1. Evaluating supported model architectures for each type of conversion [(*link*)](../../../Examples/converter_examples/Tested_Models)
2. Benchmarking quantized TensorFlow Lite models on Android platform [(*link*)](../../../Examples/converter_examples/Convert_Benchmark)
3. Profiling performances of converted models using Auptimizer Profiler [(*link*)](../../../Examples/converter_examples/Convert_Profiler)

Please check these examples for better utilization of Converter.


### Known Issues
- Limited support on certain model architectures
- Quantization for TensorFlow Lite conversion can lead to [significant accuracy loss](https://github.com/tensorflow/tensorflow/issues/40000)
