# -*- coding: utf-8 -*-
import factory

from accounts.factories import CustomUserFactory
from projects.models import Project, ProjectBuild, ProjectConfig, ProjectRelease, ProjectVolume


class ProjectFactory(factory.DjangoModelFactory):

    user = factory.SubFactory(CustomUserFactory)
    name = factory.Sequence(lambda a: "project-name{0}".format(a))
    git_repo = factory.Sequence(lambda a: "git@repo.git.com:home/{0}.git".format(a))
    git_id_rsa = factory.Sequence(lambda a: "git_id_rsa{0}".format(a))
    cpus = factory.Sequence(lambda a: float(1))
    mem = factory.Sequence(lambda a: float(512))
    instances = factory.Sequence(lambda a: int(1))

    class Meta:
        model = Project


class ProjectBuildFactory(factory.DjangoModelFactory):

    project = factory.SubFactory(ProjectFactory)
    tag = factory.Sequence(lambda a: "tag{0}".format(a))

    class Meta:
        model = ProjectBuild


class ProjectConfigFactory(factory.DjangoModelFactory):

    project = factory.SubFactory(ProjectFactory)
    key = factory.Sequence(lambda a: "key-{0}".format(a))
    value = factory.Sequence(lambda a: "value-{0}".format(a))

    class Meta:
        model = ProjectConfig


class ProjectReleaseFactory(factory.DjangoModelFactory):

    project = factory.SubFactory(ProjectFactory)
    build = factory.SubFactory(ProjectBuildFactory)

    class Meta:
        model = ProjectRelease


class ProjectVolumeFactory(factory.DjangoModelFactory):

    project = factory.SubFactory(ProjectFactory)
    container_path = factory.Sequence(lambda a: "/container_path/{0}".format(a))
    host_path = factory.Sequence(lambda a: "/host_path/{0}".format(a))

    class Meta:
        model = ProjectVolume
