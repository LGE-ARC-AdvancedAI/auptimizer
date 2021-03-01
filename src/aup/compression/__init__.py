"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""
# The actual Compressor class used
from .Compressor import *
from .utils import run_non_automatic_experiment

# Utilities
try:
    from .torch.utils import sensitivity_analysis
    from .torch.utils import shape_dependency 
    from .torch.utils import mask_conflict
    from .torch.utils import counter
except (ImportError):
    logger.debug("Could not import pytorch for compression. " +
                 "Make sure pytorch is installed if you intend to use pytorch during compression.")