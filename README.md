# ![Auptimizer Logo](AuptimizerBlackLong.png)

[![Documentation](https://img.shields.io/badge/doc-reference-blue.svg)](https://LGE-ARC-AdvancedAI.github.io/auptimizer)
[![GPL 3.0 License](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://opensource.org/licenses/GPL-3.0)
[![Build Status](https://travis-ci.com/LGE-ARC-AdvancedAI/auptimizer.svg?branch=master)](https://travis-ci.com/LGE-ARC-AdvancedAI/auptimizer)
[![coverage report](https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer/branch/master/graph/badge.svg)](https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer)

**Auptimizer** is an optimization tool for Machine Learning (ML) that automates many of the tedious parts of the model building and deployment process.
Currently, **Auptimizer** helps with:

+ **Getting the best models in minimum time** - Generate optimal models and achieve better performance by employing
state-of-the-art hyperparameter optimization (HPO) and model compression techniques. Auptimizer will run and record sophisticated HPO and model compression experiments on compute resources of your choice with effortless consistency and reproducibility.

+ **Making your models edge-ready** - Get model-device compatibility and enhanced on-device performance by converting models into the industry-standard ONNX and TensorFlow Lite formats. Auptimizer-Converter provides validated conversion techniques to ensure worry-free format transformations.

+ **Selecting the most suitable model for your edge deployment effortlessly** - Compare how different models will perform under specific compute and memory constraints on a CPU-based edge device. Auptimizer-Profiler will help you identify the most efficient models without the hustle of going through multiple physical deployment cycles.

Best of all, **Auptimizer** offers a consistent interface that allows users to switch between different HPO and compression algorithms, conversion frameworks, and computing resources with minimal changes to the existing code.

## What's New in Auptimizer v2.0
Auptimizer v2.0 introduces two core capabilites - Dashboard and Compressor!

### Dashboard

[**Auptimizer Dashboard**](https://lge-arc-advancedai.github.io/auptimizer/dashboard.html) is a powerful analytics tool that complements Auptimizer's core hyperparameter optimization (HPO) and model compression capabilities. It provides insightful visualizations to help you track experiment progress, analyze and contrast jobs, experiments, and optimization approaches. Additionally, it can be used to control an experiment or even set up a new Auptimizer environment.

### Compressor
[**Compressor**](https://lge-arc-advancedai.github.io/auptimizer/compression_main.html) is a model compression tool that helps reduce memory complexity and inference time of neural networks. It is particularly useful for adapting ML models for deployment on resource-constrained edge devices.

Similar to Auptimizer-Hyperparameter Optimization (HPO), Compressor aims to provide a unified interface to the existing state-of-the-art toolkits. Currently, Compressor leverages [NNI (version 2.0)](https://nni.readthedocs.io/en/latest/model_compression.html) model compression modules. NNI is an open-source toolkit that supports two types of compression, pruning and quantization, for TensorFlow, and PyTorch models. In the future, we will be integrating other off-the-shelf toolkits to expand the selection of model compression approaches.

## Capabilities
### Hyperparameter Optimization

Auptimizer automates tedious experimentation by performing and recording hyperparameter optimization experiments. Auptimizer provides a single seamless access point to top-notch HPO algorithms, including Bayesian optimization and multi-armed bandit. You can even integrate your own proprietary solution. Moreover, with Auptimizer, you can make the best use of your compute-resources. Whether you are using a couple of GPUs or AWS, Auptimizer will help you orchestrate compute resources for faster hyperparameter tuning. 

The table below shows a full list of currently supported techniques and resources for hyperparameter optimization.

| Supported HPO Algorithms      | Supported Infrastructure |
| ----------- | ----------- |
| Random<br>Grid<br>[Hyperband](https://github.com/zygmuntz/hyperband)<br>[Hyperopt](https://github.com/hyperopt/hyperopt)<br>[Spearmint](https://github.com/JasperSnoek/spearmint)<br>[BOHB](https://github.com/automl/HpBandSter)<br>[EAS (experimental)](https://github.com/han-cai/EAS)<br>Passive      | Multiple CPUs<br>Multiple GPUs<br>Multiple Machines (SSH)<br>AWS EC2 instances |


### Profiler
[**Profiler**](https://lge-arc-advancedai.github.io/auptimizer/profiler.html) is a simulator for profiling performance of machine learning model scripts. Given compute- and memory resource constraints for a CPU-based Edge device, Profiler can provide estimates of compute and memory usage for model scripts on the device. These estimations can be used to choose the best performing models or, in certain cases, to predict how much compute and memory models will use on the target device. 

Because Profiler mimics the target device environment on the user's development machine, the user can gain insights into the performance and resource needs of a model script without having to deploy it on the target device. Profiler helps accelerate the model selection cycle and simplifies finding model-device fit. Please see [Profiler](https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/src/aup/profiler) for usages.

### Converter
[**Converter**](https://lge-arc-advancedai.github.io/auptimizer/dlconvert.html) is a format conversion tool for machine learning models. It encapsulates best practices of individual machine learning model conversions under a single API. Converter makes ML models suitable for edge (on-device) deployments by transforming them into the industry-standard ONNX and TensorFlow Lite formats and reducing model size through quantization.

## Install

**Auptimizer** currently is well tested on Linux systems, it may require some tweaks for Windows users.

```
pip install auptimizer
```

**Note** Dependencies are not included. Using `pip install`
[requirements.txt](https://github.com/LGE-ARC-AdvancedAI/auptimizer/blob/master/requirements.txt) will install
necessary libraries for all functionalities.

Usage for the UI dashboard:
```
dashboard --path <Auptimizer database path> --port <frontend port>
```

## Documentation

See more in [documentation](https://lge-arc-advancedai.github.io/auptimizer/) 

## Example

```
cd Examples/demo
# Setup environment (Interactively create the environment file based on user input)
python -m aup.setup
# Setup experiment
python -m aup.init
# Create training script - auto.py
python -m aup.convert origin.py experiment.json demo_func
# Run aup for this experiment
python -m aup experiment.json
```

Each job's hyperparameter configuration is saved separately under `jobs/*.json` and is also recorded in the SQLite file `.aup/sqlite3.db`.

![gif demo](docs/images/demo.gif)

More examples are under [Examples](https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples).

## License

[GPL 3.0 License](./LICENSE)


## Cite

If you have used this software for research, please cite the following paper (accepted at IEEE Big Data 2019):

```
@misc{liu2019auptimizer,
    title={Auptimizer -- an Extensible, Open-Source Framework for Hyperparameter Tuning},
    author={Jiayi Liu and Samarth Tripathi and Unmesh Kurup and Mohak Shah},
    year={2019},
    eprint={1911.02522},
    archivePrefix={arXiv},
    primaryClass={cs.LG}
}
```
