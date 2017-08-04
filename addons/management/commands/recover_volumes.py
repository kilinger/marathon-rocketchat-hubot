# -*- coding:utf-8 -*-
import json
import re
import sys

from django.conf import settings
from django.core.management import BaseCommand
from sseclient import SSEClient

from addons.models import Addon
from addons.tasks import recover_volumes


class Command(BaseCommand):
    help = (
        "Can be run as a cronjob or directly to clean out expired sessions "
        "(only with the database backend at the moment)."
    )

    def handle(self, **options):

        for addon in Addon.objects.all_with_deleted().filter(deleted=True).all():
            print 'Try to recover volumes for addons', addon
            try:
                recover_volumes(addon)
            except Exception as e:
                print e

        url = settings.MARATHON_SERVERS[0] + "/v2/events"

        if settings.MARATHON_USERNAME and settings.MARATHON_PASSWORD:
            client = SSEClient(url, auth=(settings.MARATHON_USERNAME, settings.MARATHON_PASSWORD))
        else:
            client = SSEClient(url)

        for event in client:
            try:
                # logger.error("received event: {0}".format(event))
                # marathon might also send empty messages as keepalive...
                if (event.data.strip() != ''):
                    # marathon sometimes sends more than one json per event
                    # e.g. {}\r\n{}\r\n\r\n
                    for real_event_data in re.split(r'\r\n', event.data):
                        data = json.loads(real_event_data)
                        print "received event of type {0}".format(data['eventType'])
                        if data['eventType'] == 'app_terminated_event':
                            app_id = data['appId']   # /jldd-wond-meiye
                            try:
                                name, namespace = app_id[1:].rsplit("-", 1)
                            except Exception, e:
                                print 'Error', e
                                continue

                            print 'Try to recover volumes for addons', app_id
                            try:
                                addon = Addon.objects.all_with_deleted().get(name=name, namespace=namespace)
                            except Addon.DoesNotExist:
                                continue

                            if addon.deleted:
                                try:
                                    recover_volumes(addon)
                                except Exception, e:
                                    print e

                else:
                    print "skipping empty message"
            except:
                print event.data
                print "Unexpected error:", sys.exc_info()[0]
