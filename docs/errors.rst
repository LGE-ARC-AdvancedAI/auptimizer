Errors and Solutions
====================

Setup stage
-----------

+ ``Failed to load environment template %s using ConfigParser``

  Check the input ``env.ini`` template for potential mistakes or typos.

+ ``SQL engine XXX is not implemented``

  Currently only ``sqlite`` is supported.

+ ``Cant' find XXX file for resource XXX``

  The resource file is not found for Auptimizer

+ ``Error while finding module specification for XXX``

  XXX can be either ``aup.init`` or ``aup.setup``.  Double check whether you put the `aup.py` file for remote execution in your PYTHONPATH instead of the `aup` package.
