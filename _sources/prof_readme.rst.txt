Profiler
========

**Profiler is a simulator for profiling performance of Machine Learning
(ML) model scripts.** Given compute- and memory resource constraints for
a CPU-based Edge device, Profiler can provide estimates of compute- and
memory usage for model scripts on the device. These estimations can be
used to choose best performing models or, in certain cases, to predict
how much compute and memory models will use on the target device.
Because Profiler mimics the target device environment on the user’s
development machine, the user can gain insights about the performance
and resource needs of a model script without having to deploy it on the
target device.

Currently, Profiler can be used to:

1. **Select the most efficient model for your target deployment.** With
   Profiler, you can compare how different models will perform under
   specific compute and memory constraints. Our studies show that the
   ranking of models based on runtime or memory use under Profiler
   mirrors the ranking on a device with the same constraints.

2. **Make model script performance and resource requirements at the Edge
   more transparent.** Use Profiler to estimate model script’s runtime
   or memory usage on a device. For similar classes of models (such as
   different versions of MobileNet or ShuffleNet), there is a straight
   line fit between model performance under Profiler and on the target
   device. Once you run two or three models on the device, you can use
   the results to find that straight line and predict a new model’s
   performance with Profiler.

3. **Foster lean ML model deployment at the Edge.** By using Profiler,
   you can assess model-device compatibility and select the most
   suitable model for your needs without the hustle of going through
   multiple physical deployment cycles.

How Profiler Works
------------------

1. **Simulates Device Constraints.** Profiler allows developers to
   simulate different **compute** and **memory** constraints for the
   execution of the application. This is especially useful for ML model
   deployment, where testing on different edge devices can be tedious
   and require actual deployment to individual devices to ensure
   resource constraints are satisfied. Profiler can help easily
   *approximate* these constraints on a single host device.

2. **Provides Container Support.** Profiler encapsulates the
   application, its requirements, and corresponding data into a Docker
   container. It uses user inputs to build a corresponding Docker Image
   so the application can run independently and without external
   dependencies. It can then easily be scaled and ported to ease future
   development and deployment. Profiler also removes the need for a
   developer to acquaint themselves with internal workings of Docker.

3. **Logs Resource Utilization.** Profiler also tracks and records
   various resource utilization statistics of the application for
   debugging purposes. It currently tracks Average CPU Utilization,
   Memory Usage, and Block I/O. The logger also supports setting the
   ``Sample Time`` to control how frequently Profiler samples
   utilization statistics from the Docker container.

We have conducted over 300 experiments across multiple models, devices,
and compute settings. Full results are available
`here. <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples/experiments>`__


How to Use Profiler
-------------------

Installation and Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Profiler is automatically installed as part of Auptimizer, further
requiring only Docker installation. Please refer to `Docker
installation <https://docs.docker.com/install/>`__ on how to install
Docker on your system.

Using Profiler
~~~~~~~~~~~~~~

Using Profiler is simple and requires only a few steps. Once Docker and
Auptimizer are installed, all you need to do is: 

1. Ensure that the prerequisites below are met 
2. Set up the Profiler user variables in ``env.template`` 
3. Have a script that will train or perform inference on your model 
4. run ``python -m aup.profiler`` on your model file(s) (multiple models can be provided as a comma-separated list using the ``-m`` or ``--modellist`` flags or as in a txt file using the ``-f`` or ``--modelfile`` flags)

**Profiler flags:** 

1. -e or –environment : path to the environment file. 
2. -f or –modelfile : path to the text file containing different model names on new lines. 
3. -m or –modellist : list of model names as comma(‘,’) separated string (no spaces).

Prerequisites
~~~~~~~~~~~~~

The following prerequisites help to simplify the profiling procedure.
Experienced users should feel free to modify it as needed.

1. Consolidate your project into a single directory, such that the
   primary application can run without any internal dependencies (the
   data itself can be in a separate location).
2. Consolidate your application into a single entry point for execution.
   Use a wrapper file if needed. This single point of entry is needed
   because Profiler will execute one command to run a single application
   file. The application can accept different models as input.

Set Up Profiler User Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Profiler can accept two arguments as inputs - the environment file
(necessary) and model name list or file (optional). Refer to
``env_mnist.template`` and ``env_benchmark.template`` in `Profiler
Examples <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples>`__ for examples.

Create ``env.template``, and add the following variables as needed:

1.  ``IMAGEREPO`` - **REQUIRED** Enter the name of base Docker
    repository to use. Refer to https://hub.docker.com/ for public
    repositories. Your base image could be anything from
    ``tensorflow:1.3.0``, ``python3``, ``ubuntu`` etc.

2.  ``APTREQUIREMENTS`` - **OPTIONAL** Enter all linux packages required
    to run the application as a space-separated string. For example
    “curl vim”. These packages will be installed using the command
    ``apt-get install`` so ensure the packages are supported. This
    variable can also be left empty (using "").

3.  ``PIPREQUIREMENTS`` - **OPTIONAL** Enter all python libraries
    required to run the application as a space-separated string. For
    example “ipython numpy”. These packages will be installed using the
    command ``pip install``, so ensure the libraries are supported. This
    variable can also be left empty (using “”).

4.  ``PRERUN`` - **OPTIONAL** Enter commands to execute before running
    the applicati0on. ``PRERUN`` can be used to install any libraries
    that cannot be installed through ``APTREQUIREMENTS`` or
    ``PIPREQUIREMENTS``. For example, if you need a different version of
    a library than what is available through pip, you can use PRERUN to
    install it. See ``env_benchmark.template`` for an example.

5.  ``DIR`` - **REQUIRED** Enter the local path to the users
    consolidated directory containing the application. This directory
    will be copied over to the Docker container.

6.  ``SCRIPT`` - **REQUIRED** The name of the primary application file,
    along with the path relative to the aforementioned ``DIR``. This
    allows the container to find and execute the application file.

7.  ``COMMAND`` - **REQUIRED** The command used to execute the
    aforementioned script. For example ``python``.

8.  ``SAMPLETIME`` - **REQUIRED** The wait period in seconds, when
    Profiler will query the Docker for resource utilization. Avoid using
    time periods smaller than 3 seconds since Profiler internally uses
    the ``docker stats`` command which takes approximately 3 seconds to
    finish. User can use decimal points.

9.  ``OUTPUTFILE`` - **REQUIRED** The name of the file which will
    contain all the resource utilization logs with timestamps.

10. ``DOCFILE`` - **REQUIRED** The name of a user-defined Dockerfile,
    path relative to Profiler directory. This command will supersede all
    previous variables and build the Docker image from the ``DOCFILE``.
    The user should only use this variable if they have already tested
    their Dockerfile with the application to make sure they are
    compatible.

11. ``DOCKCPUS`` - **OPTIONAL** The amount of CPU processing compute
    power allowed to the application. Must be real number. Can be a
    floating point decimal. For example “2.5”. Refer to
    https://docs.docker.com/config/containers/resource_constraints/. Can
    be empty - no CPU constraint.

12. ``DOCKMEMORY`` - **OPTIONAL** The amount of memory allowed to the
    application. Must be a positive integer, followed by a suffix of b,
    k, m, g, to indicate bytes, kilobytes, megabytes, or gigabytes . For
    example “156m”. Refer to
    https://docs.docker.com/config/containers/resource_constraints/. Can
    be empty - no memory constraint.

13. ``DOCK_ARGS`` - **OPTIONAL** Additional Docker-related arguments are
    added here. For instance, to allow Docker to run the container with
    the Privileged tag, use ``--privileged``. Refer to
    https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities.
    To use volume to mount additional folder (e.g. data folder), use
    ``-v /path/in/source:/path/in/destination``.

If your primary application needs external model weight files as
arguments, you can further provide a list of the names of model weight
files. This list can be provided as a list of comma(‘,’) separated
strings of the model names or a text file with strings of the model
names, each on a new line.

Interpreting Results
--------------------

A summary of each Profiler run can be found in ``out.txt`` (the filename
can be user-specified using the ``OUTPUTFILE`` argument in the
environment file).

The individual model ``OUTPUTFILE``\ s contain the raw values of
different metrics profiled at distinct ``SAMPLETIME`` intervals using
``docker stats`` as a subroutine (https://docs.docker.com/engine/reference/commandline/stats/)

Each row contains the following values:

1. Name - name of the Docker container.
2. CPU % - the instantaneous cpu utilization (https://docs.docker.com/config/containers/resource_constraints/).
3. MEM USAGE / LIMIT - the instantaneous memory utilization and corresponding limit (https://docs.docker.com/config/containers/resource_constraints/).
4. NET I/O - refers to network input/output, the total amount of data the container has sent and received (https://docs.docker.com/engine/reference/commandline/stats/).
5. BLOCK I/O - refers to the amount of data the container has read to and written from block devices (this could be memory external to the container or to actual HDD use) on the host (https://docs.docker.com/engine/reference/commandline/stats/).
6. TIME - the current timestamp of the measurement.

The Usage Stats table shows the average utilization over the container’s
lifetime for the aforementioned CPU % and MEM USAGE / LIMIT. For NET I/O
and BLOCK I/O the total input/output data metrics are returned, instead
of the average statistics.

The final usage stats from each run of Profiler is appended to
``OUTPUTFILE`` and provides a quick overview of the result of running
Profiler multiple times.

Examples
--------

We present some examples on how to use profiler in
`Profiler
Examples <https://github.com/LGE-ARC-AdvancedAI/auptimizer/tree/master/Examples/profiler_examples>`__ folder.


TensorFlow Lite Inference Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

MNIST Training Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
