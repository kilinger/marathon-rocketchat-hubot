# -*- coding: utf-8 -*-
"""
:copyright: (c) 2015 by the xxxxx Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function
from hubot.utils.mesos import clean_container_path


class AddonsMixin(object):

    addon_name = "addon"
    addon_depend = None
    addon_container_image = "library/busybox"
    addon_default_version = "latest"

    addon_config_vars = []

    def get_addon_slug(self):
        return NotImplemented

    def get_addon_id(self):
        return NotImplemented

    def get_color(self):
        return NotImplemented

    def get_host(self, suffix=True):
        if suffix:
            return "{0}.weave.local".format(self.get_addon_id())
        else:
            return "{0}".format(self.get_addon_id())

    def get_plugin_volume_name(self, path):
        return "{0}-{1}".format(self.get_addon_slug(), clean_container_path(path))

    def get_plugin_volumes(self):
        paths = getattr(self, 'addon_container_paths', [])
        return list("{0}:{1}".format(self.get_plugin_volume_name(path), path) for path in paths)

    def get_docker_parameters(self):
        parameters = [dict(key="label", value="weave_hostname={0}".format(self.get_host(suffix=False)))]

        volumes = self.get_plugin_volumes()
        if volumes:
            parameters.append(dict(key="volume-driver", value="rexray"))
            for volume in volumes:
                parameters.append(dict(key="volume", value=volume))
        return parameters

    def get_config_vars(self):
        return self.addon_config_vars

    def get_config(self, primary=True, alias=None):
        config = dict()

        for var in self.get_config_vars():
            var = var.upper()
            if primary:
                key = var
            else:
                parts = var.split('_')
                parts.insert(-1, self.get_color().upper())
                key = '_'.join(parts)

            if alias:
                key = alias.upper()

            func = getattr(self, "get_config_{0}".format(var.lower()), None)
            if func:
                config[key] = func()
        return config

    def has_snapshot_support(self):
        return bool(self.get_plugin_volumes())

    def create_snapshot(self, description=None):
        from addons.models import AddonSnapshot

        snapshot = AddonSnapshot.objects.create(addon=self, description=description or '')
        snapshot.create(description=description)
        return snapshot

    def destroy_snapshot(self, snapshot_short_id):
        from addons.models import AddonSnapshot

        try:
            snapshot = AddonSnapshot.objects.get(addon=self, short_id=snapshot_short_id)
        except AddonSnapshot.DoesNotExist:
            pass
        else:
            snapshot.destroy()
