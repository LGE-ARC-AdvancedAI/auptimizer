Examples
========

We present some examples on how to use profiler in
`Profiler
Examples <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples>`__ folder.


TensorFlow Lite inference benchmarking
--------------------------------------

To use Profiler on TensorFlow Lite Inference Benchmarking classification
in the `benchmark <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples/bench>`__ folder.

1. [Optional] Use the bench/download.sh script (wget must be installed on your system) to download mobilenet_v1_0.75_224 and
   mobilenet_v1_1.0_224 (Alternatively, you can download a different set of TensorFlow Lite models from
   (https://www.tensorflow.org/lite/guide/hosted_models) and save them
   in `benchmark <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples/bench>`__ folder.)

2. If needed, change arguments in ``env_benchmark.template``.

3. Run ``python -m aup.profiler -e env_benchmark.template -m mobilenet_v1_0.75_224.tflite,mobilenet_v1_1.0_224.tflite``.

This will create Docker images ``mobilenet_v1_0.75_224_img`` and
``mobilenet_v1_1.0_224_img`` and corresponding Docker containers
``mobilenet_v1_0.75_224_con`` and ``mobilenet_v1_1.0_224_con``. It will
execute ``test_perf.py`` within these containers using the
``Docker Volume`` command to run inference on the specified models. Once
execution finishes, Profiler will output the following statistics:

::

   Final Usage Stats
   NAME                   AVG CPU %      PEAK CPU  AVG MEM USAGE / LIMIT    PEAK MEM    NET I/O          BLOCK I/O        TOTAL TIME (ms)
   ---------------------  -----------  ----------  -----------------------  ----------  ---------------  -------------  -----------------
   mobilenet_v1_0.75_224  225.09%          226.68  117.9 MiB / 1.9 GiB      117.9 MiB   742.0 B / 0.0 B  0.0 B / 0.0 B               6164
   mobilenet_v1_1.0_224   244.258%         250.83  122.4 MiB / 1.9 GiB      126.9 MiB   766.0 B / 0.0 B  0.0 B / 0.0 B              12354

The results from each timestamp and each individual model are saved in
``model_name``\ +\ ``out.txt`` (can be user-defined via ``OUTPUTFILE``
in ``env_benchmark.template``). Additionally, a general summary is
provided in ``out.txt`` containing the final stats for all the tested
models.

MNIST training benchmarking
---------------------------

You can also use Profiler to profile training. MNIST classification
example can be found in the `mnist <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples/mnist>`__ folder.

1. [Optional] Download the MNIST dataset from
   (http://yann.lecun.com/exdb/mnist/). Add the ``.gz`` files to the
   data folder. Then open ``env_mnist.template`` file and edit the
   ``DOCKER_ARGS`` option with the absolute path to the ``data`` folder
   as ``-v /data/:/mnist_data``.

2. Change other arguments in the ``env_mnist.template`` if you want.

3. Run ``python -m aup.profiler -e env_mnist.template``.

This will create a Docker Image named ``test_image``, and a
corresponding Docker Container ``test_container``. It will execute
``mnist.py`` within the container using Docker Volume command to load
the data. Once the execution finishes, the Profiler will output the
following statistics:

::

   Final Usage Stats
   NAME            AVG CPU %      PEAK CPU  AVG MEM USAGE / LIMIT    PEAK MEM    NET I/O              BLOCK I/O        TOTAL TIME (ms)
   --------------  -----------  ----------  -----------------------  ----------  -------------------  -------------  -----------------
   test_container  316.532%         337.98  502.3 MiB / 1.9 GiB      537.0 MiB   12.0 MiB / 151.4 kB  0.0 B / 0.0 B             220842

The results from each timestamp are saved in ``out.txt`` (set via
``OUTPUTFILE`` in ``env_mnist.template``).