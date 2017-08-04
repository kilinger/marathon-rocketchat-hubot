# -*- coding:utf-8 -*-
import json
import random
import re
import math
import time
import sys
from datetime import datetime
from django.conf import settings
from django.core.management import BaseCommand
from django.dispatch import receiver
import requests
from addons.models import Addon
from projects.models import Project, ProjectRelease
from api.utils import client
from hubot.signals import status_update_event, deployment_success
from hubot.utils.mesos import marathon


class Command(BaseCommand):
    help = (
        "Can be run as a cronjob or directly to clean out expired sessions "
        "(only with the database backend at the moment)."
    )

    def handle(self, **options):

        while True:
            for server in settings.MARATHON_SERVERS:
                try:
                    url = server + "/v2/events"

                    if settings.MARATHON_USERNAME and settings.MARATHON_PASSWORD:
                        auth = (settings.MARATHON_USERNAME, settings.MARATHON_PASSWORD)
                    else:
                        auth = None
                    response = requests.get(url, stream=True, auth=auth, headers={
                                            'Cache-Control': 'no-cache', 'Accept': 'text/event-stream'})

                    for line in response.iter_lines():
                        try:
                            if line.strip() != '':
                                # marathon sometimes sends more than one json per event
                                # e.g. {}\r\n{}\r\n\r\n
                                for real_event_data in re.split(r'\r\n', line):
                                    if real_event_data[:6] == "data: ":
                                        data = json.loads(real_event_data[6:])
                                        print "received event of type {0}".format(data['eventType'])
                                        if data['eventType'] == 'status_update_event':
                                            status_update_event.send(sender=self.__class__, data=data)
                                        elif data['eventType'] == 'deployment_success':
                                            deployment_success.send(sender=self.__class__, data=data)
                            else:
                                print "skipping empty message"
                        except:
                            print line
                            print "Unexpected error:", sys.exc_info()[0]
                except:
                    print "Caught exception! Reconnecting..."
                    time.sleep(random.random() * 3)


def addon_status_update(name=None, namespace=None,
                        version=None, status=None, **kwrags):
    try:
        addon = Addon.objects.get(name=name, namespace=namespace, m_version=version)
    except Addon.DoesNotExist:
        return

    addon.status = status
    addon.save()


def app_status_update(name=None, namespace=None,
                      version=None, status=None, timestamp=None, **kwrags):

    try:
        project = Project.objects.get(name=name, namespace=namespace)
    except Project.DoesNotExist:
        return

    release = ProjectRelease.objects.get(project=project, m_version=version)

    if status == ProjectRelease.STATUS.Finished and decide_intervel_time_to_rollback(timestamp, version):
        release.status = ProjectRelease.STATUS.Failed
        release.save()
        release.do_rollback()
        return
    release.status = status
    release.save()


def decide_intervel_time_to_rollback(timestamp, version):
    pattern = "%Y-%m-%dT%H:%M:%S.%fZ"
    interval = datetime.strptime(timestamp, pattern) - datetime.strptime(version, pattern)
    second = settings.TIMEOUT_FOR_STATUS_FINISHED
    if second > interval.seconds:
        return True
    return False


@receiver(status_update_event, sender=Command, dispatch_uid="status_update_event")
def status_update(sender, data, **kwargs):
    task_status = data['taskStatus'][5:].capitalize()  # TASK_RUNNING
    if task_status in ['Starting', 'Lost', 'Killed']:
        return

    app_id = data['appId']
    try:
        name, namespace = app_id[1:].rsplit("-", 1)  # /meimor-m-meiye
    except:
        return
    timestamp = data['timestamp']
    version = data['version']
    kw = {
        'name': name,
        'namespace': namespace,
        'version': version,
        'timestamp': timestamp,
        'status': task_status
    }
    app = marathon.get_app(app_id)

    key = app_id + ":" + version
    client.sadd(key, timestamp)
    count_now = client.scard(key)
    count_calculate = int(math.ceil(settings.MINIMUM_HEALTH_CAPACITY * app.instances))
    if app.instances > 1 and count_now < count_calculate:
        return
    client.expire(key, settings.TIMEOUT_FOR_STATUS_FINISHED)
    if 'addon' in app.labels:
        addon_status_update(**kw)
    elif 'HAPROXY_GROUP' in app.labels and task_status == ProjectRelease.STATUS.Finished:
        app_status_update(**kw)


@receiver(deployment_success, sender=Command, dispatch_uid="deployment_success")
def deployment_success_status_update(sender, data, **kwargs):
    try:
        obj = ProjectRelease.objects.get(deployment_id=data['id'])
    except ProjectRelease.DoesNotExist:
        try:
            obj = Addon.objects.get(deployment_id=data['id'])
        except Addon.DoesNotExist:
            return
    obj.status = ProjectRelease.STATUS.Running
    obj.save()
    if isinstance(obj, ProjectRelease):
        ProjectRelease.objects.filter(project=obj.project, status=ProjectRelease.STATUS.Running).exclude(
            id=obj.id).update(status=ProjectRelease.STATUS.Finished)
