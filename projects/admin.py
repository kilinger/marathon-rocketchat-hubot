# -*- coding: utf-8 -*-
import logging
from django.contrib import admin

from hubot.utils.mesos import get_image_fullname
from projects.models import Project, ProjectConfig, ProjectRelease, ProjectPort, ProjectAddon, ProjectVolume, \
    ProjectBuild
from projects.tasks import release_deploy, release_suspend


logger = logging.getLogger(__name__)


def project_release(modeladmin, request, queryset):
    for query in queryset:
        release = query.get_running_release()
        if release:
            release_deploy(release.id, enqueue=True)
project_release.short_description = "Releases all selected projects"


def project_suspend(modeladmin, request, queryset):
    for query in queryset:
        release = query.get_running_release()
        if release:
            release_suspend(release.id, enqueue=True)
project_suspend.short_description = "Suspend all selected projects"


def release_rebuild(modeladmin, request, queryset):
    for release in queryset:
        image_name = get_image_fullname(release.get_container_image())
        build = release.build
        build.do_build(image_name)
release_rebuild.short_description = "Rebuild all selected release"


def build_rebuild(modeladmin, request, queryset):
    for build in queryset:
        release, create = ProjectRelease.objects.get_or_create(build=build)
        image_name = get_image_fullname(release.get_container_image())
        build.do_build(image_name)
build_rebuild.short_description = "Rebuild all selected build"


class ProjectConfigInline(admin.TabularInline):
    model = ProjectConfig


class ProjectPortInline(admin.TabularInline):
    model = ProjectPort


class ProjectAdmin(admin.ModelAdmin):
    model = Project
    actions = [project_suspend, project_release]
    list_display = ('name', 'created', 'user', 'git_repo', 'git_id_rsa', 'cpus', 'mem', 'instances')
    search_fields = ('name', 'created', 'user__username', 'git_repo', 'git_id_rsa', 'cpus', 'mem', 'instances')
    inlines = [ProjectConfigInline, ProjectPortInline]


admin.site.register(Project, ProjectAdmin)


class ProjectVolumeAdmin(admin.ModelAdmin):

    model = ProjectVolume
    list_display = ('project', 'container_path', 'is_block_volume')
    search_fields = ('project__name', 'container_path', 'is_block_volume')

admin.site.register(ProjectVolume, ProjectVolumeAdmin)


class ProjectReleaseAdmin(admin.ModelAdmin):
    model = ProjectRelease
    actions = [release_rebuild]
    list_filter = ('status', )
    list_display = ('project', 'status', 'build', 'created', 'modified')
    search_fields = ('created', 'build__tag', 'project__name')


admin.site.register(ProjectRelease, ProjectReleaseAdmin)


class ProjectBuildAdmin(admin.ModelAdmin):
    model = ProjectBuild
    actions = [build_rebuild]
    list_filter = ('status', )
    list_display = ('project', 'status', 'tag', 'created', 'modified')
    search_fields = ('created', 'tag', 'task_id', 'project__name')


admin.site.register(ProjectBuild, ProjectBuildAdmin)


class ProjectAddonAdmin(admin.ModelAdmin):

    model = ProjectAddon

    list_display = ('project', 'addon')
    search_fields = ('project__name', 'addon__name')


admin.site.register(ProjectAddon, ProjectAddonAdmin)
