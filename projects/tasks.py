# -*- coding: utf-8 -*-
from __future__ import absolute_import
from celery import shared_task
from django.conf import settings
from marathon import MarathonHttpError
import requests
from hubot.utils.mesos import create_or_update_marathon_app, suspend_marathon_app
from projects.models import ProjectRelease, ProjectBuild
from projects.utils import LOG


@shared_task(ignore_result=True)
def release_deploy(release_id, force=False, enqueue=False, retries=5):
    try:
        release = ProjectRelease.objects.get(id=release_id)
    except ProjectRelease.DoesNotExist:
        LOG.error("Project release #{0} does not exist".format(release_id))
    else:
        LOG.info("Try to release #{0}".format(release_id))
        try:
            create_or_update_marathon_app(release, force)
        except MarathonHttpError as e:
            LOG.error(str(e))
            if enqueue and retries == 0:
                release.status = ProjectRelease.STATUS.Failed
                release.save()
                return
            countdown = 0
            if enqueue and retries and e.status_code in ["409", 409]:
                countdown = settings.TIMEOUT_FOR_STATUS_FINISHED
            release_deploy.apply_async(args=[release.id, force, enqueue, retries - 1], countdown=countdown)


@shared_task(ignore_result=True)
def release_suspend(release_id, force=False, enqueue=False, retries=5):
    try:
        release = ProjectRelease.objects.get(id=release_id)
    except ProjectRelease.DoesNotExist:
        LOG.error("Project release #{0} does not exist".format(release_id))
    else:
        LOG.info("Try to release #{0}".format(release_id))
        try:
            suspend_marathon_app(release, force)
        except MarathonHttpError as e:
            if enqueue and retries:
                release_suspend.apply_async(args=[release.id, force, enqueue, retries - 1],
                                            countdown=settings.TIMEOUT_FOR_STATUS_FINISHED)
            else:
                if enqueue and retries == 0:
                    release.status = ProjectRelease.STATUS.Failed
                    release.save()
                LOG.error(str(e))


@shared_task(ignore_result=True)
def check_build_status(task_id):
    try:
        build = ProjectBuild.objects.get(task_id=task_id)
    except ProjectBuild.DoesNotExist as e:
        LOG.error(str(e))
        return
    url = settings.EREMETIC_URL + "/" + task_id
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers,
                                auth=(settings.EREMETIC_USERNAME, settings.EREMETIC_PASSWORD))
    except Exception as e:
        LOG.error(str(e))
    else:
        status = response.json()["status"][-1]["status"][5:].capitalize()
        if build.status == ProjectBuild.STATUS.Staging and status in ProjectBuild.STATUS and build.status != status:
            build.status = status
            build.save()
            if status == ProjectBuild.STATUS.Finished:
                release = ProjectRelease.objects.get_or_create(build=build)[0]
                release_deploy.apply_async(args=[release.id, False, True])
