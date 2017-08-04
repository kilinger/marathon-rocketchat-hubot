# -*- coding: utf-8 -*-
from cinderclient import client
from django.conf import settings


class AddonNotFound(Exception):
    pass


ADDONS_REGISTRY = {

}


def addons_registry(cls):
    ADDONS_REGISTRY[cls.addon_name] = cls
    return cls


def addons_create(user, addon_name, name, cpus=None, mem=None, version=None, size=None, backup_hour=None,
                  backup_minute=None, backup_enable=None, backup_keep=None):
    if addon_name not in ADDONS_REGISTRY:
        raise AddonNotFound(u"Addons {0} not found".format(addon_name))

    cpus = float(cpus or 1)
    mem = float(mem or 512)
    size = int(size or 16)
    backup_hour = int(backup_hour or 0)
    backup_minute = int(backup_minute or 0)
    backup_keep = int(backup_keep or 7)
    backup_enable = bool(backup_enable or False)
    klass = ADDONS_REGISTRY[addon_name]

    if klass.addon_depend:
        depend = addons_create(user, klass.addon_depend, '', cpus=cpus, mem=mem, size=size, backup_hour=backup_hour,
                               backup_minute=backup_minute, backup_keep=backup_keep, backup_enable=backup_enable)
    else:
        depend = None

    version = version or klass.get_default_version()
    addon = klass(user=user, name=name, cpus=cpus, mem=mem, version=version, depend=depend, volume_size=size,
                  backup_hour=backup_hour, backup_minute=backup_minute, backup_keep=backup_keep,
                  backup_enable=backup_enable)
    addon.save()
    return addon


def get_support_addons():
    return ADDONS_REGISTRY


def get_cinder():
    cinder = client.Client('2', settings.OS_USER_NAME, settings.OS_PASSWORD,
                           settings.OS_TENANT_NAME, settings.OS_AUTH_URL)
    return cinder
