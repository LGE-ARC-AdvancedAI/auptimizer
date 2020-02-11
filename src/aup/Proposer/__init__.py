"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later
"""
import importlib
import logging

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

SPECIAL_EXIT_PROPOSERS = ("bohb","hyperband")


def get_proposer(proposer):
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
    cls = getattr(mod, proposer)
    return cls
