# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from ipaddress import IPv4Network

from projects.models import ProjectConfig, ProjectBuild, ProjectPort
from projects.serializers import ProjectConfigSerializer, ProjectBuildSerializer

NET = IPv4Network(u'10.32.0.0/12')
ALL_SUBNETS = list(NET.subnets(10))


LOG = logging.getLogger(__name__)


def get_subnet():
    # from accounts.models import CustomUser
    # while True:
    #     ix = random.randint(0, len(ALL_SUBNETS))
    #     if not (0 <= ix < len(ALL_SUBNETS)):
    #         continue
    #     subnet = ALL_SUBNETS[ix].with_prefixlen
    #     if CustomUser.objects.filter(subnet=subnet).exists():
    #         continue
    #     return subnet
    return "net:10.32.0.0/12"


def parse_env(env):
    envs = {}
    for e in env:
        e = e.split("=")
        if len(e) == 2:
            envs[e[0]] = e[1]
    return envs


def create_or_updata_env(serializer):
    project_id = serializer.data["id"]
    env = serializer.initial_data.get('env', [])
    envs = parse_env(env)
    for key, value in envs.iteritems():
        serializer_env = ProjectConfigSerializer(data=dict(project=project_id, key=key, value=value))
        if not serializer_env.is_valid():
            raise ValidationError(detail=dict(envs=serializer_env.errors))
        env_list = ProjectConfig.objects.filter(project_id=project_id, key=key.upper())
        if env_list.exists():
            for env in env_list:
                env.value = value
                env.save()
        else:
            serializer_env.save()
        serializer.data["envs"][key.upper()] = value


def create_or_updata_port(serializer):
    project_id = serializer.data["id"]
    ports = serializer.initial_data.get('port', [])
    if ports:
        for port in ports:
            ProjectPort.objects.get_or_create(project_id=project_id, port=port)
        serializer.data["ports"] = ports


def create_or_update_build(project_id, tag, serializer=None, partial=False):
    data = {"project": project_id} if project_id else {}
    if tag:
        data["tag"] = tag
    if serializer and partial:
        build = get_object_or_404(ProjectBuild, pk=serializer.data["build"]["id"])
        serializer = ProjectBuildSerializer(build, data=data, partial=partial)
    else:
        serializer = ProjectBuildSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()
