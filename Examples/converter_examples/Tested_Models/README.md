# Model Coverage
In this example, we have evaluated the capabilities and limitations of Converter conversion functions by applying the tool to select models in various supported formats.  

We tested the official models hosted/released by TensorFlow or PyTorch. Our goal was to cover as many models as possible. However, due to the limited availability of officially released models and the large number of model architectures, this evaluation does not aim to test all models exhaustively. Rather, its purpose is to identify and address common model conversion issues.

**We strongly recommended reviewing model coverage and known issues for the specific conversions, before you start using Converter.**

## How to run the evaluation tests
- *Step 0*: Make sure you have installed required packages listed in [dlconvert_requirement.txt](../dlconvert_requirements.txt).  

- *Step 1*: Prepare test models.   
There are two ways to get the test models: 1) Direct download via URLs and 2) Create the models using Python scripts.  

To download models, run `python download_models.py`. This will automatically download models from the URLs list in `download_urls.json` and save them into a `test_models` folder. The downloaded models are in Protobuf, Checkpoint or Savedmodel formats.  

To create models, run `python create_test_models.py`. This will create Keras and PyTorch models and save them into the `test_models` folder.

- *Step 2*: Convert test models to TensorFlow Lite/ONNX.  
The configuration json files for each type of conversion (from one source format to either TensorFlow Lite or ONNX) are located in [conversion_jsons](/conversion_jsons). You can run model conversion with each json file individually to test a certain conversion; e.g., 
   ```bash
   python3 -m aup.dlconvert -f conversion_jsons/convert_keras_to_onnx.json
   ```
In the json files, we set `skip:True` for the models that were tested but failed the conversion.

## Model support and known issues
Here we share the findings from the evaluation test for each individual conversion function. The model names corresponds to their names in `download_models.py` or `create_test_models.py`.

For the failed models, some failures were caused by non-supported operators in the conversion tool, while others by more model-specific issues that Converter cannot handle. Any model that is not listed below has not been tested.

If not specified, the (un)supported models apply to both TensorFlow v2.3 and TensorFlow v1.15. Please make sure you are using the TensorFlow version no lower than v1.15 to run the tests.



### Savedmodel to TensorFlow Lite
- Supported:  
resnet_50_TF2, efficientnet_b1_TF2, lstm, gru

- Not supported:  
Non-supported operators: object detection models from [TensorFlow 2 Detection Model Zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md), transformer models  
Model-specific issues: ssd_mobilenet_v1_coco, ssd_mobilenet_v2_coco

- Known issues:  
  - This conversion is only supported by Tensorflow v2.x.   
  - For some models downloaded from [TensorFlow Hub](https://tfhub.dev/) in Savedmodel format, the signature is empty. Conversion from Savedmodel format requires non-empty signature and tag.

### Savedmodel to ONNX
- Supported:  
resnet_50_TF2, efficientnet_b1_TF2, lstm, gru, ssd_mobilenet_v1_coco, ssd_mobilenet_v2_coco

- Not supported:  
Non-supported operators: object detection models from [TensorFlow 2 Detection Model Zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md), transformer models

- Known issues:   
  - This conversion is only supported by Tensorflow v2.x.   
  - Conversion from Savedmodel format requires non-empty signature and tag.

### Protobuf to TensorFlow Lite
- Supported:  
densenet, squeezenet, nasnet_mobile, inception_v3, mobilenet_v1_0.25_224  

- Not supported:  
Non-supported input type uint 8: ssd_mobilenet_v1, ssd_mobilenet_v2

- Known issues:  
  - Conversion requires correct input_nodes name and output_nodes name. When using the [summarize graph tool](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms#inspecting-graphs), you can get the names correctly. But you need to make them into format `input_name:0` or `output_name:0`; i.e., adding `:0` after the name you found from the summarize graph tool.
  - The model to be converted and the input should be in float32 format.
  - Issue with Tensorflow v1.15: None dimension is only allowed for the 1st dimension of the input. When saving model to protobuf, please specify input dimension.

### Protobuf to ONNX
- Supported:  
densenet, squeezenet, nasnet_mobile, inception_v3, mobilenet_v1_0.25_224, ssd_mobilenet_v1, ssd_mobilenet_v2

- Known issues:  
  - Conversion requires correct input_nodes name and output_nodes name. When using the [summarize graph tool](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/graph_transforms#inspecting-graphs), you can get the names correctly. But you need to make them into format `input_name:0` or `output_name:0`; i.e., adding `:0` after the name you found from the summarize graph tool.

### Keras to TensorFlow Lite
- Supported: 
VGG16, ResNet50, InceptionV3, MobileNet, MobileNetV2, DenseNet121, NASNetMobile, gru (supported by TF v2.3 only)

- Not supported:  
Model-specific conversion error: lstm

- Known issues:
  - Need to set parameter `quantization: opsset` to `tf` to enable successful conversion.

### Keras to ONNX
- Supported:  
VGG16, ResNet50, MobileNet, MobileNetV2, DenseNet121, NASNetMobile, lstm, gru (supported by TF v2.3 only), InceptionV3 (supported by TF v1.15 only)

### Checkpoint to TensorFlow Lite
- Known issues:
  - This conversion is experimental. There is no direct conversion tool available. Therefore, the approach taken is to convert a checkpoint file to frozen protobuf first, then to TensorFlow Lite. Hence, this conversion can be fragile. 

### Checkpoint to ONNX
- Supported:  
mobilenet_v1_0.25_224, ssd_mobilenet_v1, ssd_mobilenet_v2, lstm

### PyTorch to TensorFlow Lite
- Supported:  
all **image classification** models in [torchvision.models](https://pytorch.org/docs/stable/torchvision/models.html#)

- Not supported:  
Non-supported operators: fcn_resnet50, deeplabv3_resnet50, rnn models, resnet_3d, resnet_MC, resnet(2+1)d (the last three models all have 3D convolution layers)

- Known issues:  
  - To use the converter properly, please make changes in your `~/.keras/keras.json`: 
  ```bash
  "backend": "tensorflow", 
  "image_data_format": "channels_first"
  ```
  - Models with `BatchNorm2d`/`BatchNorm3d` layers are not supported in TF v1.15.

### PyTorch to ONNX
- Supported:  
all **image classification**, **semantic segmentation**, and **video classification** models in [torchvision.models](https://pytorch.org/docs/stable/torchvision/models.html#)

- Not supported:  
Non-supported operators: rnn models

- Known issues:
  - For supported models, all models can be converted using `torch==1.5.1` and `torchvision==0.6.1`, while some models fail when using `torch==1.6.0` and `torchvision==0.7.0`.
  - Models with `BatchNorm2d`/`BatchNorm3d` layers are not supported in TF v1.15.

## More resources
Auptimizer model conversion tools integrates [TFLite converter](https://www.tensorflow.org/lite/convert), [tf2onnx](https://github.com/onnx/tensorflow-onnx), [keras2onnx](https://github.com/onnx/keras-onnx), and [pytorch2keras](https://github.com/nerox8664/pytorch2keras) packages. Please check those resources for more info on model support.
