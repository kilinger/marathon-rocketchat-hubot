# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time
import logging
import datetime
import pytz
from celery import shared_task
from hubot.celery import app
from django.conf import settings
from marathon import MarathonHttpError
from addons.models import Addon
from addons.utils import get_cinder
from celery_once import QueueOnce
from hubot.utils.mesos import create_or_update_marathon_app

logger = logging.getLogger('hubot')


def recover_volumes(addon):
    cinder = get_cinder()

    for vol in addon.real_addon.get_plugin_volumes():
        name = vol.split(":")[0]
        try:
            volume = cinder.volumes.find(name=name)
            volume.delete()
        except Exception, e:
            logger.error(str(e))


@shared_task(ignore_result=True)
def create_volume_and_release(real_addon, enqueue=False, retries=5, timeout=300):
    start = time.time()

    if real_addon.get_plugin_volumes():

        while True:
            now = time.time()
            real_addon.create_volume()
            if now - start >= timeout:
                real_addon.status = Addon.STATUS.Failed
                real_addon.save()
                return
            if not real_addon.check_volume_status():
                time.sleep(10)
                continue
            break

    try:
        create_or_update_marathon_app(real_addon)
    except MarathonHttpError as e:
        if enqueue and retries:
            create_volume_and_release.apply_async(args=[real_addon, enqueue, retries - 1],
                                                  countdown=settings.TIMEOUT_FOR_STATUS_FINISHED)
        else:
            if enqueue and retries == 0:
                real_addon.status = Addon.STATUS.Failed
                real_addon.save()
            logger.error(str(e))


@shared_task(ignore_result=True)
def do_reset(real_addon):
    try:
        real_addon.reset()
    except Exception as e:
        logger.error(str(e))


@shared_task(ignore_result=True)
def restore_addon_snapshot(real_addon, snapshot, timeout=300):
    start = time.time()
    while True:
        now = time.time()
        if now - start >= timeout:
            real_addon.status = Addon.STATUS.Failed
            real_addon.save()
            return
        if not real_addon.prepare_restore(snapshot):
            continue

        output = snapshot.restore(run_async=False)
        while isinstance(output, list):
            now = time.time()
            if now - start >= timeout:
                real_addon.status = Addon.STATUS.Failed
                real_addon.save()
                return
            output = snapshot.restore(output, run_async=False)
            continue
        return


@app.task
def create_snapshot_task():
    for addon in Addon.objects.filter(backup_enable=True):
        addon = addon.real_addon
        if addon.has_snapshot_support():
            tzinfo = pytz.timezone(addon.user.tzinfo) if addon.user.tzinfo else pytz.timezone(settings.CELERY_TIMEZONE)
            now = datetime.datetime.now(tz=tzinfo)
            start = datetime.datetime(now.year, now.month, now.day, hour=addon.backup_hour, minute=addon.backup_minute)
            start = tzinfo.localize(start)
            create_snapshot.apply_async(args=[addon], eta=start, expires=now + datetime.timedelta(days=1))


@shared_task(ignore_result=True, base=QueueOnce, once={'graceful': True, 'unlock_before_run': True})
def create_snapshot(real_addon):
    description = "auto backup"
    try:
        real_addon.create_snapshot(description=description)
    except Exception as e:
        logger.error(str(e))
        return

    number = real_addon.backup_keep
    snapshots = real_addon.snapshots.all()
    counts = snapshots.count()
    if counts > number:
        short_ids = snapshots.order_by("short_id")[:counts - number].values_list("short_id", flat=True)
        for short_id in short_ids:
            real_addon.destroy_snapshot(short_id)
