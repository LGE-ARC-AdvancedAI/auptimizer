"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.PassiveResourceManger
=====================================

Leave the user to run script interactively.

+ It supports only one job running at a time.
+ It prints the command on the screen and asks user to return the value

APIs
----
"""
import logging
import os

from six.moves import input

from .AbstractResourceManager import AbstractResourceManager

logger = logging.getLogger(__name__)


class PassiveResourceManager(AbstractResourceManager):
    def __init__(self, connector, *args, **kwargs):
        super(PassiveResourceManager, self).__init__(connector, *args, **kwargs)
        self.running = False

    def get_available(self, username, rtype):
        if not self.running:
            rid = super(PassiveResourceManager, self).get_available(username, rtype)
            if rid:
                return rid
            else:
                logger.fatal("Resource passive is exhausted.  Free it from the database or create more for testing.")
                return None
        else:
            return None

    def run(self, job, rid, exp_config, call_back_func, **kwargs):
        job.verify_local()
        self.running = True
        config_path = os.path.join(job.path, "jobs", "%d.json" % job.jid)
        job.config.save(config_path)
        value = input("""# Job running path is %s
        # Config is at %s
        Job command is:
        %s
        Please run the job and manually type in results:\n""" % (job.path, config_path, job.script))
        value = float(value)
        self.running = False
        call_back_func(value, job.jid)
