# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import time
from celery import shared_task
from addons.models import Addon
from hubot.utils.mesos import marathon
from projects.models import ProjectRelease


logger = logging.getLogger("hubot")


@shared_task(ignore_result=True)
def check_release_status(deployment_id):
    try:
        release = ProjectRelease.objects.get(deployment_id=deployment_id)
    except ProjectRelease.DoesNotExist as e:
        logger.error(str(e))

    else:
        deployment_ids = [deployment.id for deployment in marathon.list_deployments()]
        if deployment_id in deployment_ids:
            release.status = ProjectRelease.STATUS.Failed
            release.save()
            release.do_rollback()
        else:
            release.status = ProjectRelease.STATUS.Running
            release.save()
            ProjectRelease.objects.filter(project=release.project, status=ProjectRelease.STATUS.Running).exclude(
                id=release.id).update(status=ProjectRelease.STATUS.Finished)


@shared_task(ignore_result=True)
def check_addon_status(deployment_id):
    try:
        addon = Addon.objects.get(deployment_id=deployment_id)
    except Addon.DoesNotExist as e:
        logger.error(str(e))

    else:
        deployment_ids = [deployment.id for deployment in marathon.list_deployments()]
        if deployment_id in deployment_ids:
            addon.status = ProjectRelease.STATUS.Failed
            addon.save()
        else:
            addon.status = ProjectRelease.STATUS.Running
            addon.save()


@shared_task(ignore_result=True)
def check_release_suspend(tag, timeout=500):
    try:
        release = ProjectRelease.objects.get(build__tag=tag)
    except Addon.DoesNotExist as e:
        logger.error(str(e))
    else:
        start = time.time()
        app = marathon.get_app(release.marathon_app_id)
        while app.instances != 0:
            now = time.time()
            if now - start >= timeout:
                release.do_rollback()
                return
            time.sleep(1)
            app = marathon.get_app(release.marathon_app_id)
            continue
        release.status = ProjectRelease.STATUS.Suspend
        release.save()


@shared_task(ignore_result=True)
def check_addon_suspend(name, timeout=500):
    try:
        addon = Addon.objects.get(name=name).real_addon
    except Addon.DoesNotExist as e:
        logger.error(str(e))
    else:
        start = time.time()
        app = marathon.get_app(addon.marathon_app_id)
        while app.instances != 0:
            now = time.time()
            if now - start >= timeout:
                addon.delete_deploy()
                return
            time.sleep(1)
            app = marathon.get_app(addon.marathon_app_id)
            continue
        addon.status = Addon.STATUS.Suspend
        addon.save()
