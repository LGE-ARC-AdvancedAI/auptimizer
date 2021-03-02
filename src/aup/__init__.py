"""
Copyright (c) 2018 LG Electronics Inc.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from .EE.Experiment import Experiment
from .aup import BasicConfig, print_result, aup_args, aup_flags, aup_save_model
import aup.compression

__version__ = "2.0"
