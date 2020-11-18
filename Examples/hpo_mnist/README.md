# HPO on MNIST data using Auptimizer

This folder contains demonstrating how to use Auptimizer for Hyperparameter Optimization on the MNIST dataset.
The original source code is from [Tensorflow Tutorial](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/examples/tutorials/mnist).
We modified `mnist_with_summaries.py` to use **Auptimizer** for model tuning.

**Tensorflow** package is needed for this demo.  
Using the CPU version will slow down the demonstration to more than 1 minute per job, but it should not be a limiting factor.

## Changes

We need to parse the input for hyperparameter values.  So we add the following lines 
to parse the values original stored in `FLAGS`, which is commonly used in `Tensorflow`
for parameter sharing.


    config = BasicConfig(**FLAGS.__dict__).load(sys.argv[1])
    FLAGS.__dict__.update(config)
    
    # for hyperband only
    if "n_iterations" in FLAGS:
    FLAGS.max_steps = int(FLAGS.n_iterations)

## Runtime

First, we could test the script with a testing configuration `demo.json`:

    python mnist_hpo.py demo.json
    
Once the script runs smoothly, it will print

    #Auptimizer:0.9592
    
At the end of the run.

Now it is the time to run **Auptimizer** for a large scale experiment.
Set up the **Auptimizer**, if you haven't done that by `python -m aup.setup <aup config>`.
Then run as `python -m aup <experiment.json>`


The following table lists the minor differences in the configuration of HPO algorithms.


| Name | Comments |
| ---- | -------- |
| Random | `n_samples` specifies the total jobs to run |
| Sequence | `n` or `interval` specifies the grid for each parameter |
| Hyperband | `max_iter` specify the total iterations for training and `engine` specify the underneath proposer |
| BOHB |  Uses many extra parameters. Refer to the documentation for details. |
| Spearmint | None |
| Hyperopt | None |

## Analysis

`MNIST Hyperparameter Optimization Demo.ipynb` presents detailed analysis of different HPO proposers under similar experimental settings for mnist.py. 

## Additional Examples - Running with AWS and Job failure capabilities.

We provide further examples to show the full array of Auptimizers capabilities to handle large scale HPO in an asynchronous cloud based distributed setting with job retry and experiment persistence capabilities.

- `exp_aws_demo.json` : Demo experiment to run MNIST HPO using AWS instances. Ensure AWS instances are registered as resources and have the correct working directory.
- `exp_aws_async.json` : Builds on the demo experiment, with a larger search space using asynchornous connections to AWS instances. Refer to the documentation for more details on async parameters.  
- `exp_aws_retry_job.json` : Builds on the demo experiment, with a larger search space on AWS instances using job failure and experiment persistence capabilities. Refer to the documentation for more details on job failure parameters.



