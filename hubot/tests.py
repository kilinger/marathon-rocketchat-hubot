# -*- coding: utf-8 -*-
import os
from django.test import TestCase
from accounts.factories import CustomUserFactory
from projects.factories import ProjectFactory, ProjectVolumeFactory, ProjectReleaseFactory, ProjectBuildFactory
from projects.models import ProjectVolume


class MarathonAppMixinTest(TestCase):

    def test_get_volumes(self):

        user = CustomUserFactory()
        project = ProjectFactory(user=user)

        build = ProjectBuildFactory(project=project)
        release = ProjectReleaseFactory(build=build)

        self.assertEqual(release.get_volumes(), [])
        self.assertEqual(release.container_paths, [])

        host_path = "/app/host_path"
        container_path = "/app/container_path"
        volume = ProjectVolumeFactory(project=project, host_path="")
        self.assertEqual(ProjectVolume.objects.count(), 1)
        self.assertIn(volume, release.container_paths)
        hostpath = os.path.join("/mnt/container-volumes/",
                                release.get_marathon_app_id(),
                                volume.container_path.strip('/'))
        self.assertEqual(hostpath, release.get_volumes()[0].host_path)
        self.assertEqual(ProjectVolume.MODE.RW, release.get_volumes()[0].mode)

        volume.delete()
        volume = ProjectVolumeFactory(project=project, host_path=host_path, container_path=container_path,
                                      mode=ProjectVolume.MODE.RO)
        self.assertEqual(ProjectVolume.objects.count(), 1)
        self.assertIn(volume, release.container_paths)
        self.assertIn(volume.host_path, release.get_volumes()[0].host_path)
        self.assertEqual(ProjectVolume.MODE.RO, release.get_volumes()[0].mode)
