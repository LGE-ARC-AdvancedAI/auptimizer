Install and setup **Auptimizer**
================================

First Time
----------

Installation
~~~~~~~~~~~~

**Auptimizer** has been well tested on the Linux environment. It has not been well tested under Windows and there is the potential for bugs.

*NOTE*: To avoid potential issues with version or permission, use :code:`virtualenv` or :code:`pip install --user` for local installation.

Run the following command from :code:`bash` to install **Auptimizer**::

  git clone <source code repo link>
  cd Auptimizer
  pip install -r requirements.txt
  python setup.py install

Environment Setup
~~~~~~~~~~~~~~~~~

Currently, **Auptimizer** relies on an environment folder to access the system resources and track experiment history.
Using `python -m aup.setup` will guide you through the setup steps.
And :doc:`environment` has more detailed explanation on the different configurations.

There are two places to save the environment file, **Auptimizer** will first search the folder named `.aup` in your working folder (where you run your command) and then your home folder (`~`).
Otherwise, you specify it at runtime with the `--aup` argument.
An error will be thrown if it is not found.

Now, you are ready to use **Auptimizer** for your experiment.  See :doc:`experiment` to learn how to change your code.
