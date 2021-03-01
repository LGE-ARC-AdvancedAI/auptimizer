# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# Modified work Copyright (c) 2018 LG Electronics Inc.
# SPDX-License-Identifier: GPL-3.0-or-later

from . import LevelPrunerMasker, SlimPrunerMasker, L1FilterPrunerMasker, \
    L2FilterPrunerMasker, FPGMPrunerMasker, TaylorFOWeightFilterPrunerMasker, \
    ActivationAPoZRankFilterPrunerMasker, ActivationMeanRankFilterPrunerMasker

MASKER_DICT = {
    'level': LevelPrunerMasker,
    'slim': SlimPrunerMasker,
    'l1': L1FilterPrunerMasker,
    'l2': L2FilterPrunerMasker,
    'fpgm': FPGMPrunerMasker,
    'taylorfo': TaylorFOWeightFilterPrunerMasker,
    'apoz': ActivationAPoZRankFilterPrunerMasker,
    'mean_activation': ActivationMeanRankFilterPrunerMasker
}
