Developer Guide
===============

For Machine Learning development
--------------------------------

**Auptimizer** makes it a little easier to debug your experiment / job in the following ways.

Set level of logging
~~~~~~~~~~~~~~~~~~~~

Logging can be activated using the :code:`--log` flag. (E.g. :code:`python -m aup <experiment> --log <level>`).
The following logging levels are available:

1. **error** - everything stops the process
2. **warn** - using default values
3. **info** - progress update
4. **debug** - everything else

Test in passive mode
~~~~~~~~~~~~~~~~~~~~

Change :code:`resource` in :code:`experiment.json` to :code:`"passive"` and then run::

    python -m aup <experiment config>

By doing so, **Auptimizer** will run in a passive mode where it interactively prints running script with its working
path and asks for the returned value. You should run your script in a second terminal to see whether it finishes
correctly. And then you can return that value back to **Auptimizer**\'s command line.

For Auptimizer Software Development
-----------------------------------

Environment
~~~~~~~~~~~

Either use :code:`virtualenv`::

    virtualenv testenv
    source testenv/bin/activate
    pip install -r requirements.txt
    export PYTHONPATH=`pwd`:$PYTHONPATH

or::

    export PYTHONPATH=<repo folder>:$PYTHONPATH

Unit testing
~~~~~~~~~~~~

If you make changes to the **Auptimizer** code, you can run the included unit tests to make sure that you didn't break anything.

If it's the first time you are running these tests, do::

    chmod u+x tests/EE/test_Job.py

to set the correct permissions.  You can then run the tests using::

    python -m unittest

API documentation
~~~~~~~~~~~~~~~~~

See :code:`<repo>/docs/index.rst` for more guidance on each hyperparameter optimization algorithm.

