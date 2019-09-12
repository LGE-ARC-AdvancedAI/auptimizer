# Tensorflow Iris Example

Here we demonstrate how to adopt an existing [tensorflow code](https://raw.githubusercontent.com/tensorflow/models/master/samples/core/get_started/premade_estimator.py) for **Auptimizer** using the automatic code generation tool.

## Steps
1. The original `premade_estimator.py` use two hyperparameters, `batch_size` and `train_steps`. To make the code more relevant to our hyperparameter search, we drop them as input arguments and use fixed values instead.
2. We add two hyperparameters into the `main()` function to update the number of neurons in each layer, i.e. `layer1` and `layer2`.  The model is constructed accordingly in line 51.
3. Add the return value `probability` in the `main()` function and also remove the "__main__" segments as we will create it automatically.
See `premade_estimator_hyper.py` for the changed script.
4. Write an experiment configution JSON file, such as:

```JSON
{
  "proposer": "random",
  "script": "premade_estimator_wrapper.py",
  "n_samples": 20,
  "random_seed": 1,
  "parameter_config": [
    {
      "name": "layer1",
      "range": [
        2,
        6
      ],
      "type": "int"
    },
    {
      "name": "layer2",
      "range": [
        2,
        6
      ],
      "type": "int"
    }
  ],
  "resource": "cpu",
  "n_parallel": 2,
  "target":"max"
}
```

4. Run code conversion as: `python -m aup.convert premade_estimator_hyper.py experiment_random.json main`.  The output file is saved as `premade_estimator_wrapper.py`.

Now we have the code for **Auptimizer** to tune.

## Run 


1. If you haven't setup **Auptimzier** yet, run `python -m aup.setup ../../FirstTime/env_local_template.ini` to setup a local environment for testing (with CPU only).  Then following instruction on the screen to run `python -m aup.setupdb.sqlite ./.aup/env.ini`.
2. Run **Auptimizer** as: `python -m aup experiment_demo.json`.
