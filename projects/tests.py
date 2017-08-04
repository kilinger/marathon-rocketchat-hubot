# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.conf import settings
from django.test import TestCase

from accounts.factories import CustomUserFactory
from addons.factories import AddonMySQLFactory
from projects.factories import ProjectFactory, ProjectBuildFactory, ProjectConfigFactory, ProjectReleaseFactory
from projects.models import ProjectAddon, Project


class ProjectTest(TestCase):

    def setUp(self):
        self.project = ProjectFactory()
        self.user = CustomUserFactory()

    def test_slug(self):
        user = CustomUserFactory()
        project = ProjectFactory(user=user)
        slug = u"{0}-{1}".format(project.name, user.username)
        self.assertEqual(project.slug, slug)

    def test_host(self):
        self.project.user = self.user
        host = u"{0}.{1}".format(self.project.slug, settings.HUBOT_DOMAIN)
        self.assertEqual(self.project.host, host)

    def test_project_config_with_addons(self):
        project = ProjectFactory()
        mysql = AddonMySQLFactory()

        mysql.attach(project)

        pa = ProjectAddon.objects.get(project=project, addon=mysql)

        configs = project.get_configs()

        for key, value in mysql.get_config(primary=pa.primary, alias=pa.alias).items():
            self.assertIn(key, configs.keys())
            self.assertEqual(value, configs[key])


class ProjectBuildTest(TestCase):

    def test_create(self):
        # TODO
        pass


class ProjectConfigTest(TestCase):

    def test_save(self):
        data = {"key": "test_key", "value": "test_value"}
        config = ProjectConfigFactory(key=data["key"], value=data["value"])
        self.assertEqual(config.key, data["key"].upper())


class ProjectReleaseTest(TestCase):

    def test_marathon_app_id(self):
        project = ProjectFactory()
        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)
        self.assertEqual(release.marathon_app_id, project.slug)

    def test_get_env(self):
        project = ProjectFactory()
        ProjectConfigFactory(project=project)
        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)
        env = release.get_env()
        for key, value in project.get_configs().items():
            self.assertTrue(key in env)
            self.assertEqual(env[key], value)

    def test_get_labels(self):
        project = ProjectFactory(name="demo")
        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)
        labels = release.get_labels()
        keys = labels.keys()

        self.assertTrue("HAPROXY_GROUP" in keys)
        self.assertEqual(labels["HAPROXY_GROUP"], "external")
        self.assertTrue("HAPROXY_0_VHOST" in keys)
        self.assertEqual(labels["HAPROXY_0_VHOST"], release.project.vhost)
        self.assertFalse("HAPROXY_0_REDIRECT_TO_HTTPS" in keys)
        self.assertFalse("HAPROXY_0_USE_HSTS" in keys)

        demo = Project.objects.get(name="demo")
        demo.redirect_https = True
        demo.use_hsts = True
        demo.save()
        build = ProjectBuildFactory(project=demo)
        release = ProjectReleaseFactory(build=build)
        labels = release.get_labels()
        keys = labels.keys()
        self.assertTrue("HAPROXY_0_REDIRECT_TO_HTTPS" in keys)
        self.assertEqual(labels["HAPROXY_0_REDIRECT_TO_HTTPS"], "true")
        self.assertTrue("HAPROXY_0_USE_HSTS" in keys)
        self.assertEqual(labels["HAPROXY_0_USE_HSTS"], "true")

    def test_get_docker_container(self):

        build = ProjectBuildFactory()
        release = ProjectReleaseFactory(build=build)

        container = release.get_docker_container()
        self.assertTrue(container.docker.image.endswith(release.get_container_image()))

    def test_get_ports(self):
        project = ProjectFactory()
        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)

        self.assertEqual(release.get_ports(), project.get_ports())

    def test_resource(self):
        mem = 1024
        cpus = 2
        instances = 3
        project = ProjectFactory(mem=mem, cpus=cpus, instances=instances)
        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)
        self.assertEqual(release.get_mem(), mem)
        self.assertEqual(release.get_cpus(), cpus)
        self.assertEqual(release.get_instances(), instances)
