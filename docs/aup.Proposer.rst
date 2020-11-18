aup.Proposer package
====================

The proposer is the core component to optimize hyperparameters for model training.

Use :func:`aup.Proposer.AbstractProposer.get_proposer` to initialize proposer.

All of them adopt the same interface as described below.


Proposers
---------

.. toctree::
   :maxdepth: 1

   aup.Proposer.HyperbandProposer
   aup.Proposer.HyperoptProposer
   aup.Proposer.RandomProposer
   aup.Proposer.SequenceProposer
   aup.Proposer.SpearmintProposer
   aup.Proposer.BOHBProposer
   aup.Proposer.EASProposer

.. automodule:: aup.Proposer.AbstractProposer
    :members:
    :undoc-members:
    :show-inheritance:
