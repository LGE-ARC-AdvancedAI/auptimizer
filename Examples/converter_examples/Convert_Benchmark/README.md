# Quantization Benchmarking on Android Phone

In this example, we use Converter to quantize and convert models into TensorFlow Lite format. 

We ran the experiment for image classification task using different configurations of MobileNet and obtained benchmarking results by deploying models on the LG G6 smartphone. The results reaffirm the benefits of model quantization for edge deployments in terms of inference speed and peak memory usage. 

The experiments are presented in the [Benchmark](Benchmark.ipynb) file along with figures showing model performance. To obtain the data pickle file, either run `Benchmark.ipynb` or `script_mobilenet.py`.

The script first downloads different MobileNets in the Protobuf format and converts them to TensorFlow Lite using different quantization configurations. The script also downloads the official TensorFlow Lite versions (int8 and float32) of MobileNet to compare the performance of the converted models.

To set up the mobile benchmarking pipeline please follow these steps.

### Setup

1. Android Studio / [adb](https://developer.android.com/studio/command-line/adb)

	```bash
	export PATH=$PATH:~/Library/Android/sdk/platform-tools/
	```
	
2. Compile model_benchmark

	See [step 1](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite/tools/benchmark#on-android):
	Needs Ubuntu system / Android Studio.
	
	```bash
	git clone git@github.com:tensorflow/tensorflow.git
	cd tensorflow
	bazel clean --expunge
	bazel build -c opt --config=android_arm --cxxopt='--std=c++11' tensorflow/lite/tools/benchmark:benchmark_model
	```

3. Prepare data on the phone

	See [step 2-4](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite/tools/benchmark#on-android)
	
	```
	Android/Sdk/platform-tools/adb push bazel-bin/tensorflow/lite/tools/benchmark/benchmark_model /data/local/tmp
	```
	
	If the device is not connected, follow instructions [here](https://askubuntu.com/questions/863587/adb-device-list-doesnt-show-phone)
	
	Copy model
	
	```bash
	adb push model.tflite /data/local/tmp
	```
	
4. Measure performance

	See [here](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite/tools/benchmark#parameters) for more control arguments.
	
	```bash
	adb shell /data/local/tmp/benchmark_model \
       --num_threads=4 \
       --graph=/data/local/tmp/model.tflite \
	   --warmup_runs=1 \
	   --num_runs=50
	```

