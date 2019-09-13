# ![Auptimizer Logo](AuptimizerBlackLong.png)

[![Documentation](https://img.shields.io/badge/doc-reference-blue.svg)](https://LGE-ARC-AdvancedAI.github.io/auptimizer)
[![BSD 3-Clause License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![pipeline status](https://travis-ci.org/LGE-ARC-AdvancedAI/auptimizer.svg?branch=master)](https://travis-ci.org/LGE-ARC-AdvancedAI/auptimizer)
[![coverage report](https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer/branch/master/graph/badge.svg)](https://codecov.io/gh/LGE-ARC-AdvancedAI/auptimizer)

**Auptimizer** is an optimization tool for Machine Learning (ML) that automates many of the tedious parts of the model building process.
Currently, **Auptimizer** helps with:

+ **Automating tedious experimentation** - Start using Auptimizer by changing just a few lines of your code. It will
  run and record sophisticated hyperparameter optimization (HPO) experiments for you, resulting in effortless
  consistency and reproducibility.

+ **Making the best use of your compute-resources** - Whether you are using a couple of GPUs or AWS, Auptimizer will
  help you orchestrate compute resources for faster hyperparameter tuning.

+ **Getting the best models in minimum time** - Generate optimal models and achieve better performance by employing
  state-of-the-art HPO techniques. Auptimizer provides a single seamless access point to top-notch HPO algorithms,
  including Bayesian optimization, multi-armed bandit. You can even integrate your own proprietary solution.

Best of all, **Auptimizer** offers a consistent interface that allows users to switch between different HPO algorithms
and computing resources with minimal changes to their existing code.

In the future, **Auptimizer** will support end-to-end model building for edge devices, including model compression and
neural architecture search. The table below shows a full list of currently supported techniques.

| Supported HPO Algorithms      | Supported Infrastructure |
| ----------- | ----------- |
| Random<br>Grid<br>[Hyperband](https://github.com/zygmuntz/hyperband)<br>[Hyperopt](https://github.com/hyperopt/hyperopt)<br>[Spearmint](https://github.com/JasperSnoek/spearmint)<br>[EAS (experimental)](https://github.com/han-cai/EAS)<br>Passive      | Multiple CPUs<br>Multiple GPUs<br>Multiple Machines (SSH)<br>AWS EC2 instances |


## Install

**Auptimizer** currently is well tested on Linux systems, it may require some tweaks for Windows users.

```
git clone <REPO URL>
cd <REPO FOLDER>
pip install -r requirements.txt
python setup.py install
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

[BSD 3-Clause License](./LICENSE)
