# -*- coding: utf-8 -*-
import logging
import random
import string
import uuid

import time

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from marathon import MarathonHttpError
from model_utils.models import TimeStampedModel, StatusModel
from safedelete.shortcuts import SoftDeleteMixin
from model_utils import Choices

from api.utils import get_random_hour, get_random_minute
from hubot.fields import RandomCharField
from addons.mixins import AddonsMixin
from addons.utils import addons_registry, get_cinder
from hubot.utils.mesos import MarathonAppMixin, destroy_marathon_app, create_or_update_marathon_app, \
    suspend_marathon_app
from hubot.models import MesosResourceModel, NamespaceModel, validate_size, validate_minute, validate_hour, \
    validate_backup_keep

COLOR = [
    "red", "pink", "violet", "black", "white", "gold", "green", "yellow", "blue", "gray"
]

CHINESE_ZODIAC = [
    "rat", "ox", "tiger", "hare", "dragon", "snake", "horse", "sheep", "monkey", "cock", "dog", "boar"
]


LOG = logging.getLogger('hubot')


@python_2_unicode_compatible
class Addon(AddonsMixin, MarathonAppMixin, NamespaceModel, StatusModel, MesosResourceModel, SoftDeleteMixin):

    STATUS = Choices(
        ('Staging', _(u'部署中')),
        ('Running', _(u'运行中')),
        ('Restoring', _(u'回滚中')),
        ('Resetting', _(u'重置中')),
        ('Suspend', _(u'已暂停')),
        ('Failed', _(u'部署失败')),
        ('Finished', _(u'已结束'))
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    color = models.CharField(max_length=128, blank=True, verbose_name=_(u"颜色标识"))
    slug = models.CharField(max_length=64)
    version = models.CharField(max_length=32)
    args = models.CharField(max_length=500, blank=True)
    m_version = models.CharField(max_length=128, blank=True, verbose_name=_('Marathon Version'))
    deployment_id = models.CharField(max_length=128, blank=True, verbose_name=_('Marathon Deployment Id'))
    volume_ids = models.TextField(blank=True, verbose_name=_('OpenStack Volume Ids'))
    volume_size = models.IntegerField(validators=[validate_size], verbose_name=_('OpenStack Volume Size'))

    backup_enable = models.BooleanField(default=False)
    backup_hour = models.IntegerField(default=0, validators=[validate_hour], verbose_name=_('Execute task Hour'))
    backup_minute = models.IntegerField(default=0, validators=[validate_minute], verbose_name=_('Execute task Minute'))
    backup_keep = models.IntegerField(default=7, validators=[validate_backup_keep],
                                      help_text=_('Snapshots number to keep'))

    depend = models.ForeignKey("self", blank=True, null=True)

    class Meta:
        verbose_name = _(u"Addon")

    def __str__(self):
        return "{0} {1}".format(self.slug, self.full_name())

    @property
    def force_pull_image(self):
        return True

    @classmethod
    def get_default_args(cls):
        return getattr(cls, "addon_default_args", "")

    def check_status_after(self, seconds):
        from hubot.tasks import check_addon_status
        check_addon_status.apply_async(args=[self.deployment_id], countdown=seconds)

    def check_suspend(self):
        from hubot.tasks import check_addon_suspend
        check_addon_suspend.apply_async(args=[self.name])

    def delete_deploy(self):
        from hubot.utils.mesos import marathon
        try:
            app = marathon.delete_deployment(self.deployment_id)
        except Exception as e:
            LOG.error(str(e))
        else:
            self.m_version = app['version']
            self.deployment_id = app['deploymentId']
            self.save()
            from hubot.tasks import check_addon_status
            check_addon_status.apply_async(args=[self.deployment_id],
                                           countdown=settings.TIMEOUT_FOR_STATUS_FINISHED)

    def storage_volume_ids(self, volume_ids):
        if isinstance(volume_ids, list):
            volume_ids = set(volume_ids + self.volume_ids.split(",")) if self.volume_ids else volume_ids
            self.volume_ids = ",".join(volume_ids)
            self.save()

    def exists_volume(self, name, storage=False):
        cinder = get_cinder()
        try:
            volumes = cinder.volumes.list(search_opts={"name": name})
        except Exception as e:
            volumes = None
            LOG.error(str(e))
        if volumes and storage:
            volume_ids = [volume.id for volume in volumes]
            self.storage_volume_ids(volume_ids=volume_ids)
        return True if volumes else False

    def create_volume(self):
        cinder = get_cinder()
        volume_ids = []

        for vol in self.real_addon.get_plugin_volumes():
            name = vol.split(":")[0]
            if self.exists_volume(name, storage=True):
                continue
            try:
                volume = cinder.volumes.create(self.volume_size, name=name)
                volume_ids.append(volume.id)
            except Exception as e:
                LOG.error(str(e))
        self.storage_volume_ids(volume_ids=volume_ids)

    def delete_volume(self, volumes_ids=""):
        cinder = get_cinder()
        volume_ids = volumes_ids if volumes_ids else self.volume_ids
        volume_ids = volume_ids.split(",")
        success_ids = []

        for volume_id in volume_ids:
            try:
                volume = cinder.volumes.get(volume_id)
                volume.delete()
                success_ids.append(volume.id)
            except Exception as e:
                LOG.error(str(e))
        if not volume_ids and len(volume_ids) == len(success_ids):
            self.volume_ids = ""
            self.save()
            return True
        return False

    def check_volume_attach(self, volume_ids=None):
        cinder = get_cinder()
        volume_ids = volume_ids if volume_ids else self.volume_ids
        volume_ids = volume_ids.split(",")
        success_ids = []

        for volume_id in volume_ids:
            try:
                volume = cinder.volumes.get(volume_id)
                if not volume.multiattach:
                    success_ids.append(volume.id)
            except Exception as e:
                LOG.error(str(e))

        if len(volume_ids) == len(success_ids):
            return False
        return True

    def check_volume_status(self, volume_ids=None):
        cinder = get_cinder()
        volume_ids = volume_ids if volume_ids else self.volume_ids
        volume_ids = volume_ids.split(",")
        success_ids = []

        for volume_id in volume_ids:
            try:
                volume = cinder.volumes.get(volume_id)
                if volume.status == "available":
                    success_ids.append(volume.id)
            except Exception as e:
                LOG.error(str(e))

        if len(volume_ids) == len(success_ids):
            return True
        return False

    def rename_volume(self, suffix=""):
        cinder = get_cinder()
        volume_ids = self.volume_ids.split(",")
        success_ids = []
        for volume_id in volume_ids:
            try:
                volume = cinder.volumes.get(volume_id)
                name = volume.name + "." + suffix + ".history" if suffix else volume.name + ".history"
                if not volume.name.endswith(".history"):
                    volume.update(name=name)
                success_ids.append(volume.id)
            except Exception as e:
                LOG.error(str(e))

        if len(volume_ids) == len(success_ids):
            return True
        return False

    def prepare_restore(self, snapshot):
        if self.status != Addon.STATUS.Restoring:
            self.status = Addon.STATUS.Restoring
            self.save()
        destroy_marathon_app(self, run_async=False)
        while True:
            attach = self.check_volume_attach()
            if attach:
                continue
            break
        return self.rename_volume(str(snapshot.short_id))

    def check_volume_ids(self, coverage=False):
        cinder = get_cinder()
        volume_ids = self.volume_ids.split(",")
        expect_ids = []
        for vol in self.real_addon.get_plugin_volumes():
            name = vol.split(":")[0]
            volumes = cinder.volumes.list(search_opts={"name": name})
            expect_ids = expect_ids + [v.id for v in volumes]
        if len(set(volume_ids + expect_ids)) == len(volume_ids):
            return True
        elif coverage:
            self.volume_ids = ",".join(expect_ids)
            self.save()
        return False

    def reset(self):
        addon = self.real_addon
        if addon.status != Addon.STATUS.Resetting:
            addon.status = Addon.STATUS.Resetting
            addon.save()
        addon.check_volume_ids(coverage=True)
        suspend_marathon_app(addon, run_async=False)
        while True:
            if not addon.check_volume_status():
                time.sleep(1)
                continue
            break
        delete_volume = addon.delete_volume()
        if not delete_volume:
            addon.rename_volume()
        if addon.volume_ids:
            addon.volume_ids = ""
            addon.save()
        from addons.tasks import create_volume_and_release
        create_volume_and_release.apply_async(args=[addon, True])

    def save(self, *args, **kwargs):
        if not self.color:
            self.color = random.choice(COLOR)
        if not self.slug:
            self.slug = self.get_slug()
        if not self.version:
            self.version = self.get_default_version()
        if not self.args:
            self.args = self.get_default_args()
        if not self.backup_hour:
            self.backup_hour = get_random_hour()
        if not self.backup_minute:
            self.backup_minute = get_random_minute()
        super(Addon, self).save(*args, **kwargs)

    def get_addon_slug(self):
        return self.full_name(namespace_first=False) + "-addon"

    def get_addon_id(self):
        return self.marathon_app_id

    def get_weave_cidr(self):
        return self.user.subnet

    @property
    def marathon_app_id(self):
        return self.get_addon_slug()

    def get_container_image(self):
        return "{0}:{1}".format(self.addon_container_image, self.version)

    def get_labels(self):
        return {
            "addon": self.slug
        }

    def get_upgrade_strategy(self):
        # cinder volume only can attach to one vm, so we should destroy our addons first when container migration
        return dict(minimum_health_capacity=0, maximum_over_capacity=0)

    def get_dependencies(self):
        if self.addon_depend:
            return ["/{0}".format(self.depend.marathon_app_id)]

    @classmethod
    def get_default_version(cls):
        return cls.addon_default_version

    def get_color(self):
        return self.color

    def get_slug(self):
        return getattr(self, "addon_name", "notfound")

    @property
    def real_addon(self):
        return getattr(self, "addon" + self.slug)

    def get_random_name(self):
        return "{0}-{1}".format(get_random_string(4, allowed_chars=string.lowercase), random.choice(CHINESE_ZODIAC))

    def attach(self, project, alias=None):
        from projects.models import ProjectAddon
        if alias and ProjectAddon.objects.filter(project=project, alias=alias).exists():
            raise Exception(u"Addon alias '{0}' already exists".format(alias))
        ProjectAddon.objects.create(project=project, addon=self, alias=alias or '')

    def detach(self, project=None):
        from projects.models import ProjectAddon
        if project:
            ProjectAddon.objects.filter(project=project, addon=self).delete()
        else:
            ProjectAddon.objects.filter(addon=self).delete()


@python_2_unicode_compatible
class AddonSnapshot(TimeStampedModel, models.Model):

    short_id = models.IntegerField(default=0)
    addon = models.ForeignKey(Addon, related_name='snapshots')
    snapshot_ids = models.TextField(blank=True)
    volume_ids = models.TextField(blank=True, verbose_name=_('Restore Volume Ids'))
    description = models.CharField(max_length=1000, blank=True)

    class Meta:
        verbose_name = _(u"Addon Snapshot")
        ordering = ('-short_id', '-modified')
        unique_together = (("addon", "short_id"),)

    def __str__(self):
        return "{0}-snapshot-s{1}".format(self.addon, self.created)

    def restore(self, snapshot_ids=None, run_async=True):
        cinder = get_cinder()
        addon = self.addon.real_addon
        snapshot_ids = snapshot_ids if snapshot_ids else self.snapshot_ids
        snapshot_ids = snapshot_ids.split(",")
        volume_ids = []
        success_ids = []
        for snapshot_id in snapshot_ids:
            try:
                snapshot = cinder.volume_snapshots.get(snapshot_id)
                name = snapshot.name.split("-snapshot-s")[0]
                volume = cinder.volumes.create(addon.volume_size, name=name, snapshot_id=snapshot_id)
                volume_ids.append(volume.id)
                success_ids.append(snapshot_id)
            except Exception as e:
                LOG.error(str(e))

        if not run_async:
            while True:
                if not addon.check_volume_status(volume_ids=",".join(volume_ids)):
                    time.sleep(1)
                    continue
                break
        if len(snapshot_ids) == len(volume_ids):
            if self.volume_ids:
                self.volume_ids = str(self.volume_ids) + "," + str(addon.volume_ids)
            else:
                self.volume_ids = addon.volume_ids
            self.save()
            addon.volume_ids = ",".join(volume_ids)
            addon.save()

            retries = 5
            while retries:
                try:
                    create_or_update_marathon_app(addon)
                except MarathonHttpError as e:
                    retries -= 1
                    LOG.error(str(e))
                    time.sleep(1)
                    continue
                else:
                    return True
            addon.status = Addon.STATUS.Failed
            addon.save()
            return False
        lost_ids = list(set(snapshot_ids) - set(success_ids))
        return ",".join(lost_ids)

    def save(self, *args, **kwargs):

        if not self.short_id:
            try:
                latest_snapshot = AddonSnapshot.objects.filter(addon=self.addon).order_by('-short_id')[0]
            except IndexError:
                short_id = 1
            else:
                short_id = latest_snapshot.short_id + 1

            self.short_id = short_id
        super(AddonSnapshot, self).save(*args, **kwargs)

    def create(self, description=None):

        cinder = get_cinder()

        snapshot_ids = []

        for vol in self.addon.real_addon.get_plugin_volumes():
            name = vol.split(":")[0]
            try:
                volume = cinder.volumes.find(name=name)
            except Exception as e:
                LOG.error(str(e))
            else:
                snapshot_name = "{0}-snapshot-s{1}".format(volume.name, self.short_id)
                snapshot_description = "snapshot at {0}".format(now())
                if description:
                    snapshot_description = "{0} for {1}".format(snapshot_description, description)
                snapshot = cinder.volume_snapshots.create(volume.id, force=True,
                                                          name=snapshot_name, description=snapshot_description)
                snapshot_ids.append(snapshot.id)
        if snapshot_ids:
            self.snapshot_ids = ','.join(snapshot_ids)
            self.save()

    def destroy(self):
        cinder = get_cinder()

        for snapshot_id in self.snapshot_ids.split(','):
            try:
                snapshot = cinder.volume_snapshots.get(snapshot_id)
            except Exception as e:
                LOG.error(str(e))
            else:
                cinder.volume_snapshots.delete(snapshot)

        self.addon.real_addon.delete_volume(self.volume_ids)
        self.delete()


@addons_registry
class AddonMySQL(Addon):
    addon_name = "mysql"
    addon_container_paths = ["/var/lib/mysql"]
    addon_container_image = "addons/mysql"
    addon_default_version = "5.6"
    addon_default_args = "--character-set-server=utf8"

    addon_config_vars = ["DATABASE_URL"]

    db_name = RandomCharField(max_length=32, length=6, lowercase=True, include_digits=False)
    db_user = RandomCharField(length=8, lowercase=True, include_digits=False)
    db_password = RandomCharField(length=16)

    def get_env(self):
        return {
            "MYSQL_PASSWORD": self.db_password,
            "MYSQL_USER": self.db_user,
            "MYSQL_DATABASE": self.db_name,
            "MYSQL_ALLOW_EMPTY_PASSWORD": "yes",
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_database_url(self):
        return "mysql://{username}:{password}@{host}:{port}/{db}".format(
            username=self.db_user,
            password=self.db_password,
            host=self.get_host(),
            port=3306,
            db=self.db_name)


@addons_registry
class AddonPostgresql(Addon):
    addon_name = "postgresql"
    addon_container_paths = ["/var/lib/postgresql/data"]
    addon_container_image = "addons/postgres"
    addon_default_version = "9.4"

    addon_config_vars = ["DATABASE_URL"]

    db_name = RandomCharField(max_length=32, length=6, lowercase=True, include_digits=False)
    db_user = RandomCharField(length=8, lowercase=True, include_digits=False)
    db_password = RandomCharField(length=16)

    def get_env(self):
        return {
            'DATABASES': self.db_name,
            'POSTGRES_USER': self.db_user,
            'POSTGRES_PASSWORD': self.db_password,
            'WEAVE_CIDR': self.get_weave_cidr()
        }

    def get_config_database_url(self):
        return "postgres://{username}:{password}@{host}:{port}/{db}".format(
            username=self.db_user,
            password=self.db_password,
            host=self.get_host(),
            port=5432,
            db=self.db_name)


@addons_registry
class AddonMemcached(Addon):
    addon_name = "memcached"
    addon_container_image = "addons/memcached"
    addon_default_version = "1.4"

    addon_config_vars = ["CACHE_URL"]

    def get_env(self):
        return {
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_cache_url(self):
        return "memcache://{host}:11211".format(
            host=self.get_host()
        )


@addons_registry
class AddonRedis(Addon):
    addon_name = "redis"
    addon_container_paths = ["/data"]
    addon_container_image = "addons/redis"
    addon_default_version = "2.8"

    addon_config_vars = ["REDIS_URL"]

    def get_env(self):
        return {
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_redis_url(self):
        return "redis://{host}:6379/0".format(
            host=self.get_host()
        )


@addons_registry
class AddonRabbitmq(Addon):
    addon_name = "rabbitmq"
    addon_container_paths = ["/var/lib/rabbitmq"]
    addon_container_image = "addons/rabbitmq"
    addon_default_version = "3.6"

    addon_config_vars = ["RABBITMQ_URL"]

    mq_user = RandomCharField(length=8, lowercase=True, include_digits=False)
    mq_password = RandomCharField(length=16)
    mq_vhost = RandomCharField(max_length=32, length=6, lowercase=True, include_digits=False)

    def get_env(self):
        return {
            "RABBITMQ_DEFAULT_USER": self.mq_user,
            "RABBITMQ_DEFAULT_PASS": self.mq_password,
            "RABBITMQ_DEFAULT_VHOST": self.mq_vhost,
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_rabbitmq_url(self):
        return "amqp://{username}:{password}@{host}:{port}/{vhost}".format(
            username=self.mq_user,
            password=self.mq_password,
            host=self.get_host(),
            vhost=self.mq_vhost,
            port=5672
        )


@addons_registry
class AddonElasticSearch(Addon):
    addon_name = "elasticsearch"
    addon_container_paths = ["/usr/share/elasticsearch/data"]
    addon_container_image = "addons/elasticsearch"
    addon_default_version = "1.7"
    addon_config_vars = ["ELASTICSEARCH_URL"]

    def get_env(self):
        return {
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_elasticsearch_url(self):
        return "http://{host}:9200".format(
            host=self.get_host()
        )


@addons_registry
class AddonMongodb(Addon):
    addon_name = "mongodb"
    addon_container_paths = ["/data"]
    addon_container_image = "addons/mongodb"
    addon_default_version = "3.0"
    addon_config_vars = ["MONGO_URL"]

    db_name = RandomCharField(max_length=32, length=6, lowercase=True, include_digits=False)
    db_user = RandomCharField(length=8, lowercase=True, include_digits=False)
    db_password = RandomCharField(length=16)

    def get_env(self):
        return {
            "MONGODB_USERNAME": self.db_user,
            "MONGODB_PASSWORD": self.db_password,
            "MONGODB_DBNAME": self.db_name,
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    def get_config_mongo_url(self):
        return "mongodb://{username}:{password}@{host}:{port}/{db}".format(
            username=self.db_user,
            password=self.db_password,
            db=self.db_name,
            host=self.get_host(),
            port=27017
        )


@addons_registry
class AddonInfluxdb(Addon):
    addon_name = "influxdb"
    addon_container_paths = ["/data"]
    addon_container_image = "addons/influxdb"
    addon_default_version = "0.9"
    addon_config_vars = ["INFLUXDB_URL"]

    db_name = RandomCharField(max_length=32, length=6, lowercase=True, include_digits=False)
    db_user = RandomCharField(length=8, lowercase=True, include_digits=False)
    db_password = RandomCharField(length=16)

    def get_env(self):
        return {
            "PRE_CREATE_DB": self.db_name,
            "ADMIN_USER": self.db_user,
            "INFLUXDB_INIT_PWD": self.db_password,
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    @property
    def context(self):
        return {
            "host": self.get_host(),
            "port": 8086,
            "username": self.db_user,
            "password": self.db_password,
            "db": self.db_name
        }

    def get_config_influxdb_url(self):
        return "http://{username}:{password}@{host}:{port}/{db}".format(**self.context)


@addons_registry
class AddonStatsd(Addon):
    addon_depend = "influxdb"
    addon_name = "statsd"
    addon_container_image = "addons/statsd"
    addon_default_version = "0.2.2"
    addon_config_vars = ["STATSD_URL", "STATSD_HOST", "STATSD_PORT"]

    def get_env(self):
        context = self.depend.real_addon.context
        return {
            "INFLUXDB_HOST": "http://{host}:{port}".format(**context),
            "INFLUXDB_USERNAME": context["username"],
            "INFLUXDB_PASSWORD": context["password"],
            "INFLUXDB_DATABASE": context["db"],
            "WEAVE_CIDR": self.get_weave_cidr()
        }

    @property
    def context(self):
        return {
            "host": self.get_host(),
            "port": 8125
        }

    def get_config_statsd_url(self):
        return "udp://{host}:{port}".format(**self.context)

    def get_config_statsd_host(self):
        return "{host}".format(**self.context)

    def get_config_statsd_port(self):
        return "{port}".format(**self.context)
