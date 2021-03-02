"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import importlib
import logging
from enum import Enum

logger = logging.getLogger(__name__)

PROPOSERS = {
    "random": "RandomProposer",
    "sequence": "SequenceProposer",
    "spearmint": "SpearmintProposer",
    "hyperband": "HyperbandProposer",
    "hyperopt": "HyperoptProposer",
    "bohb": "BOHBProposer",
    "eas": "EASProposer"
}

ProposerStatus = Enum('ProposerStatus', 'RUNNING FINISHED FAILED')

SPECIAL_EXIT_PROPOSERS = ("bohb","hyperband")


def get_proposer(proposer, disable_proposer_logging=False):
    """
    Create Proposer

    :param proposer: name of proposer
    :type proposer: str
    :return: A proposer class
    :rtype: AbstractProposer
    """
    logger.debug("choose %s as proposer" % proposer)
    try:
        proposer = PROPOSERS[proposer.lower()]
    except KeyError:
        logger.fatal(("%s proposer is not implemented" % proposer))
        raise ValueError("%s proposer is not implemented" % proposer)

    mod = importlib.import_module("." + proposer, "aup.Proposer")
    _logger = logging.getLogger(mod.__name__)
    _logger.disabled = disable_proposer_logging
    cls = getattr(mod, proposer)
    return cls
