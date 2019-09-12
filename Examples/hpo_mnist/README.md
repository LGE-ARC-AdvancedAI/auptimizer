# MNIST Demo

Tuning neural network for MNIST dataset.

The original code is from [Tensorflow Tutorial](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/examples/tutorials/mnist).
We modified `mnist_with_summaries.py` to use **Auptimizer** for model tuning.

**Tensorflow** package is needed for this demo.  
Using CPU version will slow down the demonstration to more than 1 minute but still tolerable.

## Changes

We need to parse the input for hyperparameter values.  So we add the following lines 
to parse the values original stored in `FLAGS`, which is commonly used in `Tensorflow`
for parameter sharing.


    config = BasicConfig(**FLAGS.__dict__).load(sys.argv[1])
    FLAGS.__dict__.update(config)
    
    # for hyperband only
    if "n_iterations" in FLAGS:
    FLAGS.max_steps = int(FLAGS.n_iterations)

## Run time

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
| Spearmint | `n_samples` as random, `size` marks dimension for each parameter |
| Hyperopt | |
| ENAS | |

