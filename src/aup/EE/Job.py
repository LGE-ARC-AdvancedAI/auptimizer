"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Job module
=================

Wrap Job information for :mod:`aup.EE.Resource` to execute.

APIs
----
"""
import logging
import os
import stat
from time import sleep

from ..utils import open_sftp_with_timeout

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

logger = logging.getLogger(__name__)


class Job:
    local_warning = True

    def __init__(self, script, config, path=".", retries=3):
        """
        Job wrapper give to resource manager to execute

        :param script: script file name
        :type script: str
        :param config: job configuration
        :type config: aup.BasicConfig
        :param path: working path
        :type path: str
        :param retries: max number of retries for one job in the case of job failure
        :type retries: int
        """
        logger.debug("Input: %s,%s", script, path)
        self.config = config
        self.path = os.path.abspath(os.path.expanduser(path))
        if script[0] not in ('.', '/'):
            script = os.path.join(".", script)
            if Job.local_warning:
                logger.warning("Using default local path for script as %s", script)
                Job.local_warning = False  # only warning once
        self.script = script
        self.jid = 0
        self.was_executed = False
        self.retries = retries
        self.curr_retries = 0
        self.rid_blacklist = set()

        # if true, it means this is the best job
        self.save_model_flag = config.get('save_model', False)

    def verify_local(self):
        """
        Verify the job script is correctly set - for local machine running only

        :return: whether all paths are set correctly
        :rtype: bool
        """
        job_path = os.path.join(self.path, "jobs")
        script = os.path.join(self.path, self.script.split()[0])  # avoid additional arguments in the script
        if not os.path.isdir(self.path):
            msg = "Working folder %s does not exist" % self.path
            logger.fatal(msg)
            raise EnvironmentError(msg)

        if not os.path.exists(job_path):  # job config file dir, also used in ResourceManagers.
            logger.warning("Create missing directory %s", job_path)
            os.makedirs(job_path)
        logger.debug("Create Job %s", script)

        if not os.path.isfile(script):
            logger.fatal("Job script %s is not exist", self.script)
            raise EnvironmentError("Missing script")
        if not os.access(script, os.X_OK):
            logger.fatal("Job script is not executable, try `chmod u+x %s`"%self.script)
            raise EnvironmentError("Wrong permission for %s" % self.script)
        return True

    def verify_remote(self, remote, overwrite=False):  # pragma: no cover
        """
        Verify the files and folder are correct on the remote machine

        :param remote: paramiko.SSHClient
        :param overwrite: whether to overwrite existing script file and folder
        :return: whether the files are set correctly
        :rtype: bool
        """

        sftp = open_sftp_with_timeout(remote.client, 5)
        local_script = self.script.split()[0]
        local_job_path = os.path.join(os.path.dirname(local_script), 'jobs')
        if not os.path.isdir(local_job_path):
            logger.warning("Create missing local job config directory %s", local_job_path)
            os.makedirs(local_job_path)
        remote_script = os.path.join(self.path, os.path.basename(self.script))
        try:
            sftp.stat(self.path)
        except FileNotFoundError:
            logger.warning("Create missing folder %s", self.path)
            sftp.mkdir(self.path)
        try:
            path = os.path.join(self.path, "jobs")
            stats = sftp.stat(path)
            if not (stats.st_mode & stat.S_IWRITE):
                logger.warning("%s/jobs is not writable, changed", path)
                sftp.chmod(path, stat.S_IWRITE)
        except FileNotFoundError:
            logger.warning("create jobs %s", os.path.join(self.path, "jobs"))
            sftp.mkdir(os.path.join(self.path, "jobs"))

        if overwrite:
            logger.info("Overwrite script %s", remote_script)
            sftp.put(local_script, remote_script)
            sftp.chmod(remote_script, stat.S_IRWXU)
        try:
            sftp.stat(remote_script)
        except FileNotFoundError:
            logger.warning("script not found, copy local file over")
            sftp.put(local_script, remote_script)
            sftp.chmod(remote_script, stat.S_IRWXU)

        stats = sftp.stat(remote_script)
        if not (stats.st_mode & stat.S_IEXEC):
            logger.warning("Assign correct permission")
            sftp.chmod(remote_script, stat.S_IRWXU)
        sftp.close()
        return True
