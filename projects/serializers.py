# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from projects.models import Project, ProjectBuild, ProjectConfig, ProjectRelease


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project

    def to_representation(self, obj):
        ret = super(ProjectSerializer, self).to_representation(obj)
        if isinstance(obj, Project):
            envs = ProjectConfigSerializer(obj.configs.all(), many=True).data
            data = {}
            for env in envs:
                data.update(env)
            ret['envs'] = data
        return ret


class ProjectBuildSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectBuild


class ProjectConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectConfig

    def to_representation(self, obj):
        ret = super(ProjectConfigSerializer, self).to_representation(obj)
        data = {ret["key"]: ret["value"]}
        return data


class ProjectDeploymentSerializer(serializers.ModelSerializer):
    app_id = serializers.ReadOnlyField(source="marathon_app_id")

    class Meta:
        model = ProjectRelease

    def to_representation(self, obj):
        ret = super(ProjectDeploymentSerializer, self).to_representation(obj)
        if isinstance(obj.build, ProjectBuild):
            build = get_object_or_404(ProjectBuild, pk=obj.build.id)
            ret["build"] = ProjectBuildSerializer(build).data
        return ret
