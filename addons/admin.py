# -*- coding: utf-8 -*-
from django.contrib import admin

from addons.models import AddonMySQL, Addon, AddonPostgresql, AddonMongodb, AddonRabbitmq, AddonInfluxdb, AddonSnapshot
from addons.tasks import create_volume_and_release
from hubot.utils.mesos import suspend_marathon_app


def addon_release(modeladmin, request, queryset):
    for query in queryset:
        addon = query.real_addon
        if query.depend:
            create_volume_and_release.apply_async(args=[addon.depend, True])
        create_volume_and_release.apply_async(args=[addon, True])
addon_release.short_description = "Releases all selected addons"


def addon_suspend(modeladmin, request, queryset):
    for query in queryset:
        suspend_marathon_app(query)
addon_suspend.short_description = "Suspend all selected addons"


class AddonAdmin(admin.ModelAdmin):
    model = Addon
    actions = [addon_suspend, addon_release]
    list_display = ('name', 'slug', 'version', 'status', 'user', 'created', 'modified', 'volume_size', 'cpus', 'mem')
    search_fields = ('name', 'slug', 'version', 'status', 'user__username', 'created', 'modified', 'volume_size')


admin.site.register(Addon, AddonAdmin)


class AddonSnapshotAdmin(admin.ModelAdmin):
    model = AddonSnapshot
    list_display = ('addon', 'description', 'short_id', 'created', 'modified')
    search_fields = ('addon__name', 'description', 'short_id', 'created', 'modified')


admin.site.register(AddonSnapshot, AddonSnapshotAdmin)


class AddonMySQLAdmin(admin.ModelAdmin):
    model = AddonMySQL
    list_display = ('name', 'user', 'created', 'modified')
    search_fields = ('name', 'user__username', 'created', 'modified')


admin.site.register(AddonMySQL, AddonMySQLAdmin)


class AddonPostgresqlAdmin(admin.ModelAdmin):
    model = AddonPostgresql
    list_display = ('name', 'user', 'created', 'modified')
    search_fields = ('name', 'user__username', 'created', 'modified')


admin.site.register(AddonPostgresql, AddonPostgresqlAdmin)


class AddonMongodbAdmin(admin.ModelAdmin):
    model = AddonMongodb
    list_display = ('name', 'user', 'created', 'modified')
    search_fields = ('name', 'user__username', 'created', 'modified')

admin.site.register(AddonMongodb, AddonMongodbAdmin)


class AddonRabbitmqAdmin(admin.ModelAdmin):
    model = AddonRabbitmq
    list_display = ('name', 'user', 'created', 'modified')
    search_fields = ('name', 'user__username', 'created', 'modified')

admin.site.register(AddonRabbitmq, AddonRabbitmqAdmin)


class AddonInfluxdbAdmin(admin.ModelAdmin):
    model = AddonInfluxdb
    list_display = ('name', 'user', 'created', 'modified')
    search_fields = ('name', 'user__username', 'created', 'modified')

admin.site.register(AddonInfluxdb, AddonInfluxdbAdmin)
