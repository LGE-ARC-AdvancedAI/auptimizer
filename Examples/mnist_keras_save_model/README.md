# Save best model feature

This example showcases how to use saving the best model feature. This feature allows the user to save the best performing model after running the HPO experiment. This is achieved by running the training script again using the best hyperparamters obtained during HPO the experiment. 
The model, by default, will be saved to path ``aup_models/models_<eid>/<user_defined_model_path>``.

## Usage

In order to use this feature, please add to the configuration file:

	"resource_args": {
		"save_model": true
  	}

Depending on whether ``@aup_args`` is used, the training script needs to be changed differently. 
Please check ``mnist.py`` and ``mnist_wo_decorator.py`` for examples of adapting the training script 
with and without using the decorator, respectively.

## Run experiment

To run the experiment on the remote machine, make sure to change the ``node.txt`` file and "workingdir" 
in ``exp_random_node.json`` to the your own settings. Then run
```sh
python -m aup.setup
python -m aup exp_random_node.json
```

To run the experiment using the local cpu, please run
```sh
python -m aup.setup cpu.ini
python -m aup exp_random_cpu.json
```

