"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

"""
import sys, importlib
from os import path
from typing import Callable

KNOWN_FLAGS=["logtostderr","alsologtostderr", "log_dir", "v", "verbosity", "stderrthreshold", "showprefixforinfo", \
    "run_with_pdb", "pdb_post_mortem", "run_with_profiling", "profile_file", "use_cprofile_for_profiling", \
    "only_check_args", "help", "helpshort", "helpfull", "helpxml", "logger_levels"]


def load_package(filename: str, function: Callable) -> Callable:
    """Load a function/class from a script "filename"
    """
    sys.path.insert(0, path.dirname(path.abspath(filename)))
    mod = path.basename(filename).rstrip(".py")
    mod = importlib.import_module(mod)
    return getattr(mod, function)


def reset_flag():
    """Reset absl.flags
    """
    from absl import flags
    FLAGS = flags.FLAGS # pylint: disable=invalid-name
    for name in list(FLAGS):
        if name not in KNOWN_FLAGS:
            delattr(FLAGS, name)
