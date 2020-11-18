"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.AWSResourceManager
==================================

APIs
----
"""
import logging
import time

import boto3
import paramiko as pm
from botocore.exceptions import ClientError

from .SSHResourceManager import SSHResourceManager, Remote, parse_hostname

logger = logging.getLogger(__name__)
logging.getLogger("botocore").setLevel(logger.getEffectiveLevel())
logging.getLogger("boto3").setLevel(logger.getEffectiveLevel())
logging.getLogger("urllib3").setLevel(logger.getEffectiveLevel())

retry = 10  # number of retries
DEFAULT_SHUTDOWN = False  # shutdown after experiment
prescript = "" # commands to be executed before script
postscript = "" # commands to be executed after script


def _is_instance_id(hostname):
    return 'i-' in hostname


class AWSRemote(Remote):  # pragma: no cover
    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')

    @classmethod
    def change_status(cls, hostnames, target='start'):
        """
        Changes status of the AWS machine depending on the target status and permissions.
        """
        if target == 'start':
            action = cls.ec2_client.start_instances
        else:
            action = cls.ec2_client.stop_instances
        try:
            action(InstanceIds=hostnames, DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' in str(e):
                logger.debug("Permission to start/stop EC2 instance granted")
            else:
                logger.fatal("You don't have permissions")
                raise e
        try:
            response = action(InstanceIds=hostnames, DryRun=False)
            logger.debug(response)
        except ClientError as e:
            logger.debug(e)
            if e.response['Error']['Code'] in ('IncorrectInstanceState'):
                retry_counter = 0
                while retry_counter < retry:
                    try:
                        response = action(InstanceIds=hostnames, DryRun=False)
                        break
                    except ClientError:
                        retry_counter += 1
                        logger.warning("Instance not yet ready for starting, retry in 30 sec (%d/%d)", retry_counter, 
                                       retry)
                        time.sleep(30)
                if retry_counter == retry:
                    logger.fatal('cannot start instance, there might be some issues')
                    raise EnvironmentError("Failed to start AWS instance with in %d retries", retry)

    @classmethod
    def verify(cls, hostname):
        """
        Verifies if instance can be loaded, returns the instance object if true.
        """
        instance = cls.ec2_resource.Instance(hostname)
        try:
            instance.load()
        except ClientError as e:
            logger.fatal("""There is an error running on instance %s
                         There can be many reasons, such as wrong instance name, insufficient permissions or
                         incorrect AWS confirmations""", hostname)
            raise e
        return instance

    def __init__(self, instance):
        """

        :param instance: string formatted according to :code:`.SSHResourceManager.parse_hostname`
        :type instance: str
        """
        super(AWSRemote, self).__init__(instance)

        if not _is_instance_id(self.hostname):  # use SSHResourceManager
            logger.debug("AWS connection profile %s %s", self.username, self.hostname)
            return

        instance = self.verify(self.hostname)
        if instance.state['Name'] == 'running':
            logger.debug('Instance is already running')
            self.hostname = instance.public_dns_name
            logger.debug("New Hostname= %s", str(self.hostname))
        else:
            logger.debug("Instance was not running, Starting instance")
            self.change_status([self.hostname])
            instance = self.ec2_resource.Instance(self.hostname)
            try:
                instance.wait_until_running()
            except Exception as e:
                logger.fatal("Catch unexpected problem with AWS instance")
                raise e
            self.hostname = instance.public_dns_name
            while instance.state['Name'] != 'running':
                logger.warning("waiting instance %s to start, wait 10 sec", instance.state['Name'])
                time.sleep(10)
                instance.load()  # additional waiting time for SSH service ready
            logger.debug('...instance is %s', instance.state['Name'])
        logger.debug("AWS connection profile %s %s", self.username, self.hostname)

    def exec_command(self, command, *args, **kwargs):
        return self.client.exec_command(command, *args, **kwargs)

    def __enter__(self):
        retry_counter = 0
        while retry_counter < retry:
            try:
                self.client.connect(hostname=self.hostname, username=self.username, pkey=self.key, timeout=180,
                                    auth_timeout=180)
                logger.debug("Connected to AWS instance")
                break
            except pm.ssh_exception.NoValidConnectionsError:
                retry_counter += 1
                logger.warning("Instance not yet ready for ssh, retry in 30 sec (%d/%d)", retry_counter, retry)
                time.sleep(30)
        if retry_counter == retry:
            logger.fatal('cannot connect to instance, there might be some issues')
            raise EnvironmentError("Failed to start AWS instance with in %d retries" % retry)
        return self


class AWSResourceManager(SSHResourceManager):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        super(AWSResourceManager, self).__init__(*args, key="aws_mapping", **kwargs)
        self.remote_class = AWSRemote
        self.shutdown = kwargs.get("shutdown", DEFAULT_SHUTDOWN)
        global retry
        retry = kwargs.get("connection_retry", retry)
        self.used_resource = set()

    def __del__(self):
        if not self.shutdown:
            logger.debug("AWS EC2 keeps running")
            return
        to_stop = []
        try:
            for rid in self.used_resource:
                _, hostname, _, _ = parse_hostname(self.mapping[rid])
                if not _is_instance_id(hostname):
                    logger.info("Not AWS instance ID, won't stop %s", hostname)
                    continue
                logger.debug("Stopping instance with name %s", hostname)
                instance = AWSRemote.verify(hostname)
                if instance.state['Name'] == 'stopped':
                    logger.warning('instance is already stopped')
                else:
                    to_stop.append(hostname)
            AWSRemote.change_status(to_stop, target='stop')
            logger.info("Following instances '%s' are stopped", ','.join(to_stop))
        except Exception as e:
            logger.fatal("Encounter error %s during shutdown, instances may not be stopped correctly", e)

    def run(self, job, rid, *args, **kwargs):
        self.used_resource.add(rid)
        super(AWSResourceManager, self).run(job, rid, *args, **kwargs)

