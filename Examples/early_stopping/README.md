# Early stopping of jobs

## Usage

In order to use early stopping to accelerate the HPO experiment,
we need to add the following lines in the JSON configuration file:

    "resource_args": 
        {
            "early_stop":
                {
                    "aup_policy": "X",
                    "aup_policy_steps": Y
                    ...
                }
        }

X can be bandit, median, truncation or curve_fitting.
Y refers to the interval of epochs/iterations by which the ES policy is applied.

In order to report intermediate results, "aup.print_result" should be called from the user script; e.g. at the end of an epoch, at the end of N iterations, etc.

Examples can be found at Examples/early_stopping/quad_equation_min and Examples/early_stopping/mnist_keras.

An additional parameter of "warmup" can also be used for all ES strategies (default is 0). "warmup" defines the number of initial iterations that should finish without an early stopping criterion.


## Strategies

We provide 4 strategies for early stopping: bandit, truncation, median and curve fitting. Please checkout [early stopping document](https://lge-arc-advancedai.github.io/auptimizer/early_stop.html) for detailed usages.

