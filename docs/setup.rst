First time installation
=======================


Installation
~~~~~~~~~~~~

**Auptimizer** has been well tested on the Linux environment. It has not been well tested under Windows and there exists the potential for issues.

*NOTE*: To avoid potential issues with version or permission, use :code:`virtualenv` or :code:`pip install --user` for local installation.

Released version
@@@@@@@@@@@@@@@@

Run the following command from :code:`bash` to install:

::

   pip install auptimizer

**Note** Dependencies are not included. Using ``pip install``
`requirements.txt <https://github.com/LGE-ARC-AdvancedAI/auptimizer/blob/master/requirements.txt>`_ will install
necessary libraries for all functionalities.

Development version
@@@@@@@@@@@@@@@@@@@

Run the following command from :code:`bash` to install the latest version of **Auptimizer**::

  git clone <source code repo link>
  cd Auptimizer
  pip install -r requirements.txt
  python setup.py install

Note: Python2 is required for `spearmint` package, and Python>3=3.6 is recommended for `BOHB` algorithm.

Environment Setup
~~~~~~~~~~~~~~~~~

Currently, **Auptimizer** relies on an environment folder to access the system resources and track experiment history.
Using `python -m aup.setup` will guide you through the setup.
:doc:`environment` has more detailed explanations about the different configurations.

There are two places you can save the environment file - **Auptimizer** will first search the folder named `.aup` in
your working folder (where you run your command) and then your home folder (`~`). Otherwise, you specify it at runtime
with the `--aup` argument. An error will be thrown if this environment file cannot be found.

You are now ready to use **Auptimizer** for your experiment.  See :doc:`experiment` to learn how to change your code.
