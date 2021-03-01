Early Stopping
==============

Early stopping (ES) strategies provide increased efficiency for HPO algorithms by reducing the computational cost. This is 
done by detecting the poor performance of certain hyperparameter settings early in the training and stopping the corresponding jobs. 
As a result, better hyperparameter configurations can be found sooner with reduced compute resources. 

ES is especially useful in the context of deep learning where the search space grows exponentially over increasing hyperparameters. 
ES strategies provide users with advanced tools to aggressively explore larger search spaces over limited resources, 
with tradeoffs between HPO speed and final model performance. 

Auptimizer provides 4 popular ES strategies namely – Bandit, Median, Truncation and Curve-Fitting, which can be applied to all Proposers.
The Bandit, Median and Curve-Fitting strategies are inspired by the following papers, while the Truncation strategy is provided to be used
as a benchmark for other ES strategies: 

===============  ==============================================================================================================================================================================================================
Strategy         Algorithm
===============  ==============================================================================================================================================================================================================
Bandit           `HYPERBAND: Bandit-Based Configuration Evaluation For Hyperparameter Optimization <https://openreview.net/pdf?id=ry18Ww5ee>`__
Median           `Google Vizier: A Service for Black-Box Optimization <https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/46180.pdf>`__
Curve-fitting    `Speeding up Automatic Hyperparameter Optimization of Deep Neural Networks by Extrapolation of Learning Curves <http://aad.informatik.uni-freiburg.de/papers/15-IJCAI-Extrapolation_of_Learning_Curves.pdf>`__
===============  ==============================================================================================================================================================================================================

Usage
@@@@@

The feature can be used by adding the following parameter to the experiment configuration file::

  "resource_args": {
    "early_stop":
        {
            "aup_policy": "bandit",
            "aup_policy_steps": 5
            ...
        }
   }
   
+ ``aup_policy``: the early stopping strategy in ["bandit", "median", "truncation" or "curve_fitting"]. 
+ ``aup_policy_steps``: integer, the interval of epochs, by which the intermediate results are compared among jobs and the ES policy is applied.

``aup_policy`` and ``aup_policy_steps`` are the two parameters required for all ES strategies. There are also strategy-specifc parameters, which will be introduced below.

In order to track the intermediate results to be used in ES, ``aup.print_result`` should be called from the user script in the training loop, e.g.::
  
  def main(*args, **kwargs):
    # model and data preparation code
    for epoch in range(10):
        # training code for one epoch
        aup.print_result(res)

Examples can be found in Auptimizer Gibhub repository at ``Examples/early_stopping/quad_equation_min`` and ``Examples/early_stopping/mnist_keras``. 

Additionally, when using ES, the ``track_intermediate_results`` feature will be triggerd automatically. This means that the resulting intermediate results will be stored in the database in the ``intermediate_results`` table and 
can be visualized via dashboard. This also means that the presence of ``track_intermediate_results`` in the experiment configuration file with any value, even false, will be ignored. 

An optional parameter of ``warmup`` can also be used for all ES strategies (default is 0). ``warmup`` defines the number of initial epochs that should finish before the ES strategy starts to apply.


Strategies
@@@@@@@@@@

Bandit
~~~~~~~

The bandit policy stops jobs that have a result lower than a specified percentage of the global best result of all jobs. This percentage is defined by the parameter ``bandit_factor``. The result to be compared among jobs is the best result obtained by 
the job up to the same epoch.

Example::

    "resource_args": 
    {
        "early_stop":
        {
            "aup_policy": "bandit",
            "aup_policy_steps": 10,
            "bandit_factor": 0.5
        }
    }

In this example, we stop jobs with the best result which is worse than 0.5 of the global best result. 
This comparison and job cut-off is carried out every 10 epochs. 
Default value for ``bandit_factor`` is 0.5, with higher values indicating more aggressive ES strategy.


Truncation
~~~~~~~~~~

The truncation policy cuts a fraction of the worst performing jobs, based on the jobs' best result obtained up to the same epoch. The fraction is specified by the parameter ``truncation_percentage``.

Example::

    "resource_args": 
    {
        "early_stop":
        {
            "aup_policy": "truncation",
            "aup_policy_steps": 10,
            "truncation_percentage": 0.6
        }
    }
    
This example stops 60% of the jobs every 10 epochs. Default value for ``truncation_percentage`` is 0.3, with higher values indicating more aggressive ES strategy. 


Median
~~~~~~~

The median policy stops the jobs that yield worse results than the median of the running average of results of all jobs up to the same epoch. 

Example::

    "resource_args": 
    {
        "early_stop":
        {
            "aup_policy": "median",
            "aup_policy_steps": 10
        }
    }
    

Curve Fitting
~~~~~~~~~~~~~~

The curve fitting policy attempts to fit each job's history to a weighted combination of multiple, pre-selected functions, in order to predict its final (best) value. It then stops jobs that fail to attain at least a threshold of the best overall result across all jobs. The implementation is adapted from `NNI <https://github.com/microsoft/nni/blob/master/docs/en_US/Assessor/CurvefittingAssessor.md>`__.

**Caveats:** the biggest downside to curve fitting is that it is usually time-consuming. This makes curve fitting less applicable for small datasets, or tasks that train quickly. In order to address this issue, users should always provide a timeout for the maximum time allowed for each curve fitting process (default: 30s). After the specified time has run out, the curve-fitting process will be stopped and the last result obtained will be used. The longer the timeout, the better the results.

Example::

    "resource_args": 
    {
        "early_stop":
        {
            "aup_policy": "curve_fitting",
            "aup_policy_steps": 10,
            "curve_fitting_threshold": 0.95,
            "curve_fitting_timeout": 60
        }
    }

Example for scripts that use ``aup.print_result`` for result reporting instead::

    "resource_args":
    {
        "early_stop":
        {
            "aup_policy": "curve_fitting",
            "aup_policy_steps": 10,
            "curve_fitting_threshold": 0.95,
            "curve_fitting_timeout": 60,
            "curve_fitting_max_iters": 100
        }
    }
    
Default values for ``curve_fitting_threshold``, ``curve_fitting_timeout`` are 0.95 and 60. ``curve_fitting_max_iters`` defaults to None.  
