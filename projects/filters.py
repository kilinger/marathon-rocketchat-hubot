# -*- coding:utf-8 -*-
import django_filters
from projects.models import Project, ProjectRelease, ProjectConfig


class ProjectFilter(django_filters.FilterSet):

    username = django_filters.CharFilter(name="user__username")

    class Meta:
        model = Project


class ProjectEnvFilter(django_filters.FilterSet):

    # project = django_filters.CharFilter(name="project_id")

    class Meta:
        model = ProjectConfig


class ProjectDeploymentFilter(django_filters.FilterSet):

    username = django_filters.CharFilter(name="project__user__username")

    class Meta:
        model = ProjectRelease
