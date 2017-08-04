# -*- coding: utf-8 -*-
"""
:copyright: (c) 2015 by the xxxxx Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from django.test import TestCase
import mock
from accounts.factories import CustomUserFactory
from addons.factories import AddonFactory, AddonMySQLFactory, AddonPostgresqlFactory, AddonMemcachedFactory, \
    AddonRedisFactory, AddonMongodbFactory, AddonRabbitmqFactory, AddonInfluxdbFactory, AddonStatsdFactory
from addons.models import AddonMySQL, Addon, AddonSnapshot
from api.views.execute import AddonsCmd, ProjectsCmd, ConfigCmd, ReleasesCmd, xxxxxCmd, SnapshotsCmd
from projects.factories import ProjectFactory, ProjectConfigFactory, ProjectReleaseFactory
from projects.models import Project, ProjectBuild


@mock.patch("api.views.execute.create_volume_and_release", mock.MagicMock(return_value=None))
@mock.patch("api.views.execute.create_or_update_marathon_app", mock.MagicMock(return_value=None))
@mock.patch("api.views.execute.destroy_marathon_app", mock.MagicMock(return_value=None))
class AddonsCmdTest(TestCase):

    def test_addons_real_addon(self):
        self.user = CustomUserFactory()
        self.project = ProjectFactory(user=self.user)
        cmd = AddonsCmd(self.user)
        cmd.run(u"create mysql -n addon -p {0}".format(self.project.name))

        self.addon = Addon.objects.get(name="addon")
        self.mysql = AddonMySQL.objects.get(addon_ptr_id=self.addon.id)
        self.assertEqual(self.mysql, self.addon.real_addon)

    def test_addons_create(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)

        rc, out, err = cmd.run(u"create mysql")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(out, cmd.usage())

        rc, out, err = cmd.run(u"create mysql -p demo")
        self.assertEqual(rc, cmd.ERROR)

        project = ProjectFactory(user=user, name="demo")

        self.assertEqual(project.addons.count(), 0)

        rc, out, err = cmd.run(u"create mysql -p {0}".format(project.name))
        self.assertEqual(rc, cmd.OK)

        self.assertEqual(project.addons.count(), 1)

        rc, out, err = cmd.run(u"create mysql -p demo --name=demo --cpus=2 --mem=1024")
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.filter(name="demo")
        self.assertTrue(addon.exists())
        self.assertEqual(addon.count(), 1)
        addon = addon[0]
        self.assertEqual(addon.cpus, 2)
        self.assertEqual(addon.mem, 1024)

        rc, out, err = cmd.run(u"create mysql -p demo --name=demo1 --cpus=2 --mem=4k")
        self.assertEqual(err, '--mem=<mem> should be float 0 < mem <= 16384')
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -p demo --name=demo --cpus=2 --mem=4")
        self.assertEqual(err, "Addon name 'demo' already exists")
        self.assertEqual(rc, cmd.ERROR)

    def test_addons_destroy(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)

        project = ProjectFactory(user=user, name="demo")

        self.assertEqual(project.addons.count(), 0)

        rc, out, err = cmd.run(u"create mysql -p {0} --name=demo".format(project.name))
        self.assertEqual(rc, cmd.OK)

        self.assertEqual(project.addons.count(), 1)

        rc, out, err = cmd.run(u"destroy".format(project.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"destroy foo".format(project.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"destroy demo".format(project.name))
        self.assertEqual(rc, cmd.OK)

        self.assertEqual(project.addons.count(), 0)

    def test_addons_attach(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        demo = ProjectFactory(user=user, name="demo")
        test = ProjectFactory(user=user, name="test")

        rc, out, err = cmd.run(u"create mysql -n addon -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 1)

        rc, out, err = cmd.run(u"attach addon -p test")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 2)
        self.assertIn("DATABASE_URL", demo.get_configs())
        self.assertIn("DATABASE_URL", test.get_configs())

        rc, out, err = cmd.run(u"attach addon -p test")
        self.assertEqual(rc, cmd.ERROR)

    def test_addons_detach(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")
        ProjectFactory(user=user, name="test")

        rc, out, err = cmd.run(u"create mysql -n addon -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 1)

        cmd.run(u"attach addon -p test")
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 2)
        rc, out, err = cmd.run(u"detach addon -p test")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 1)

        rc, out, err = cmd.run(u"detach addon -p test")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="addon").projects.all().count(), 1)

    def test_addons_all_with_name_after_destroy(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")
        ProjectFactory(user=user, name="test")

        cmd.run(u"create mysql -n demo -p demo")
        self.assertEqual(Addon.objects.filter().count(), 1)
        self.assertEqual(Addon.objects.filter(name="demo").count(), 1)

        cmd.run(u"attach demo -p test")
        cmd.run(u"detach demo -p test")
        cmd.run(u"destroy demo")

        rc, out, err = cmd.run(u"create mysql -p demo --name=demo --cpus=2 --mem=4096")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"attach demo -p test")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.filter().count(), 1)
        self.assertEqual(Addon.objects.filter(name="demo").count(), 1)
        self.assertEqual(Addon.objects.all_with_deleted().count(), 2)
        self.assertEqual(Addon.objects.deleted_only().count(), 1)

    def test_addons_create_same_name_after_destroy(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n add-mysql -p demo")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"destroy add-mysql")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create mysql -n add-mysql -p demo")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create mysql -n add-mysql -p demo")
        self.assertEqual(rc, cmd.ERROR)

    def test_addons_info(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n add-mysql -p demo")
        addon = Addon.objects.filter(name="add-mysql")
        self.assertEqual(rc, cmd.OK)
        self.assertTrue(addon.exists())

        rc, out, err = cmd.run(u'info add-mysql')
        self.assertEqual(rc, cmd.OK)
        addon = addon[0].real_addon
        self.assertIn("Addon info", out)
        self.assertIn("Name", out)
        self.assertIn(unicode(addon.name), out)
        self.assertIn("Cpus", out)
        self.assertIn(str(addon.cpus), out)
        self.assertIn("Mem", out)
        self.assertIn(str(addon.mem), out)
        self.assertIn("Service", out)
        self.assertIn(addon.addon_name, out)
        self.assertIn("Config", out)
        self.assertIn(unicode(addon.get_config())[1:-1], out)
        self.assertIn("Host", out)
        self.assertIn(addon.get_host(), out)

        rc, out, err = cmd.run(u'info mysql')
        self.assertEqual(rc, cmd.ERROR)

    def test_addons_scale(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        cpus = 2
        mem = 1024

        cmd.run(u"create mysql -n addon -p demo -c {0} -m {1}".format(cpus, mem))
        rc, out, err = cmd.run(u'scale addon')
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.get(name="addon").real_addon
        self.assertEqual(addon.cpus, cpus)
        self.assertEqual(addon.mem, mem)

        cpus = 8
        mem = 9216

        rc, out, err = cmd.run(u'scale addon -c {0} -m {1}'.format(cpus, mem))
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.get(name="addon").real_addon
        self.assertEqual(addon.cpus, cpus)
        self.assertEqual(addon.mem, mem)

        rc, out, err = cmd.run(u'scale addons')
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u'scale addon -c 1o -m ')
        self.assertEqual(rc, cmd.ERROR)

    def test_addons_service(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"services")
        self.assertEqual(rc, cmd.OK)
        self.assertIn("postgresql", out)
        self.assertIn("9.4", out)
        self.assertIn("mongodb", out)
        self.assertIn("3", out)
        self.assertIn("redis", out)
        self.assertIn("2.8", out)
        self.assertIn("rabbitmq", out)
        self.assertIn("3.6", out)
        self.assertIn("elasticsearch", out)
        self.assertIn("1.7", out)
        self.assertIn("mysql", out)
        self.assertIn("5.6", out)
        self.assertIn("memcached", out)
        self.assertIn("1.4", out)

    def test_addons_create_volume_size(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n addon -s size")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n addon -s -1")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n addon -s 99999")
        self.assertEqual(rc, cmd.ERROR)

        cpus = 2
        mem = 1024
        size = 4

        rc, out, err = cmd.run(u"create mysql -n addon -p demo -c {0} -m {1} -s {2}".format(cpus, mem, size))
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.get(name="addon").real_addon
        self.assertEqual(addon.cpus, cpus)
        self.assertEqual(addon.mem, mem)
        self.assertEqual(addon.volume_size, size)

    def test_addons_create_with_backup_enable(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-enable true")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertFalse(Addon.objects.get(name="demo").backup_enable)

        rc, out, err = cmd.run(u"create mysql -n test -p demo --backup-enable")
        self.assertEqual(rc, cmd.OK)
        self.assertTrue(Addon.objects.get(name="test").backup_enable)

    def test_addons_create_with_backup_hour(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour 33")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour -6")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour 3.5")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour 3.0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour hour")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour true")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-hour 21")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="demo").backup_hour, 21)

        rc, out, err = cmd.run(u"create mysql -n test -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertIn(Addon.objects.get(name="test").backup_hour, xrange(24))

    def test_addons_create_with_backup_minute(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute 66")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute -8")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute 54.68")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute backup-minute")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute true")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute 0.00")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-minute 44")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="demo").backup_minute, 44)

        rc, out, err = cmd.run(u"create mysql -n test -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertIn(Addon.objects.get(name="test").backup_minute, xrange(60))

    def test_addons_create_with_backup_keep(self):
        user = CustomUserFactory()
        cmd = AddonsCmd(user)
        ProjectFactory(user=user, name="demo")

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep 999999")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep -6")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep 3.5")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep 8.0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep backup-keep")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep true")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create mysql -n demo -p demo --backup-keep 10")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="demo").backup_keep, 10)

        rc, out, err = cmd.run(u"create mysql -n test -p demo")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.get(name="test").backup_keep, 7)


class ProjectCmdTest(TestCase):

    def test_project_create(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        rc, out, err = cmd.run(u"create")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        rc, out, err = cmd.run(u"create demo")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertTrue(Project.objects.filter(name="demo").exists())

        rc, out, err = cmd.run(u"create foo -c 2 -m 2048 -i 10")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 3)
        self.assertTrue(Project.objects.filter(name="foo").exists())

        foo = Project.objects.get(user=user, name="foo")
        self.assertEqual(foo.cpus, 2)
        self.assertEqual(foo.mem, 2048)
        self.assertEqual(foo.instances, 10)

        rc, out, err = cmd.run(u"create bar --cpus 8 --mem 4096 --instances 2")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 4)
        self.assertTrue(Project.objects.filter(name="bar").exists())

        rc, out, err = cmd.run(u"create bar --cpus 2 --mem 2048 --instances 10")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"create new --cpu 2 --mem 2048 -i 10")
        self.assertEqual(rc, cmd.ERROR)

    def test_project_destroy(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        project = ProjectFactory(user=user, name="demo")
        self.assertEqual(Project.objects.all().count(), 1)

        cmd.run(u"destroy {0}".format(project.name))
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"destroy {0}".format("name"))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"destroy {0}".format("name"))
        self.assertEqual(rc, cmd.ERROR)

    def test_project_info(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        project = ProjectFactory(user=user, name="info")
        rc, out, err = cmd.run(u"info {0}".format(project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"info {0}".format(project.name))
        self.assertEqual(rc, cmd.OK)

        self.assertIn("Project info", out)
        self.assertIn("Name", out)
        self.assertIn(project.name, out)
        self.assertIn("Cpus", out)
        self.assertIn(unicode(project.cpus), out)
        self.assertIn("Mem", out)
        self.assertIn(unicode(project.mem), out)
        self.assertIn("Instances", out)
        self.assertIn(str(project.instances), out)
        self.assertIn("Host", out)
        self.assertIn(project.get_host(), out)
        self.assertIn("Health check", out)
        self.assertIn(project.health_check, out)

        rc, out, err = cmd.run(u"info")
        self.assertEqual(rc, cmd.ERROR)

    def test_project_scale(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        cmd.run(u"create demo")
        rc, out, err = cmd.run(u"scale demo -c 4 -m 1024 --instances 4")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo", user=user)
        self.assertEqual(project.cpus, 4)
        self.assertEqual(project.mem, 1024)
        self.assertEqual(project.instances, 4)

        rc, out, err = cmd.run(u"scale -p demo -c 4 -m 1024 --instances 4")
        self.assertEqual(rc, cmd.ERROR)

    def test_project_list(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        rc, out, err = cmd.run(u"list")
        self.assertEqual(rc, cmd.OK)

        ProjectFactory.create_batch(10)
        rc, out, err = cmd.run(u"list")
        self.assertEqual(rc, cmd.OK)

    def test_project_health_check(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)

        rc, out, err = cmd.run(u"create project")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="project")
        self.assertEqual(project.health_check, "/")

        rc, out, err = cmd.run(u"scale project --health-check /version/")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="project")
        self.assertEqual(project.health_check, "/version/")

        rc, out, err = cmd.run(u"scale project --no-health-check")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="project")
        self.assertEqual(project.health_check, "")

        rc, out, err = cmd.run(u"create test --no-health-check")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="test")
        self.assertEqual(project.health_check, "")

        rc, out, err = cmd.run(u"scale test --health-check /version")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="test")
        self.assertEqual(project.health_check, "/version")

    def test_project_use_hsts(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)
        cmd.run(u"create demo")
        project = Project.objects.get(name="demo")
        self.assertFalse(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts t")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts f")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts true")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts false")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts y")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts n")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts yes")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.use_hsts)

        rc, out, err = cmd.run(u"scale demo --use-hsts no")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.use_hsts)

    def test_project_redirect_https(self):
        user = CustomUserFactory()
        cmd = ProjectsCmd(user)
        cmd.run(u"create demo")
        project = Project.objects.get(name="demo")
        self.assertFalse(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https t")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https f")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https true")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https false")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https y")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https n")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https yes")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertTrue(project.redirect_https)

        rc, out, err = cmd.run(u"scale demo --redirect-https no")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="demo")
        self.assertFalse(project.redirect_https)


class ConfigCmdTest(TestCase):

    def setUp(self):
        self.user = CustomUserFactory()
        self.project = ProjectFactory(user=self.user)

    def test_config_set(self):
        cmd = ConfigCmd(self.user)

        rc, out, err = cmd.run(u"set -p {0} key=value name=test test=测试 chinese=中文".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"set key=value -p {0}".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"set test=测试 -p {0}".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"set key=value name=test -p {0} test=测试 chinese=中文".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"set key value")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"set key=value")
        self.assertEqual(rc, cmd.ERROR)

    def test_config_unset(self):
        cmd = ConfigCmd(self.user)

        key = "key"
        value = "value"
        ProjectConfigFactory(project=self.project, key=key, value=value)
        rc, out, err = cmd.run(u"unset -p {0} {1}".format(self.project.name, key))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"unset")
        self.assertEqual(rc, cmd.ERROR)

        cmd.run(u"set -p {0} key=value name=test chinese=中文".format(self.project.name))
        rc, out, err = cmd.run(u"unset -p {0} chinese".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"unset -p {0} key name".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"unset -p {0} chinese".format(self.project.name))
        self.assertEqual(rc, cmd.ERROR)

    def test_config_get(self):
        cmd = ConfigCmd(self.user)

        key = "key"
        value = "value"

        cmd.run(u"set -p {0} {1}={2} test=测试".format(self.project.name, key, value))

        rc, out, err = cmd.run(u"get -p {0} {1}".format(self.project.name, key))
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(out, value)

        rc, out, err = cmd.run(u"get -p {0} test".format(self.project.name))
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(out, u"测试")

        rc, out, err = cmd.run(u"get")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"get -p {0} key test".format(self.project.name))
        self.assertEqual(rc, cmd.ERROR)

    def test_config_list(self):
        cmd = ConfigCmd(self.user)

        cmd.run(u"set -p {0} key=value test=测试 name=test_config".format(self.project.name))
        rc, out, err = cmd.run(u"list -p {0}".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run("list")
        self.assertEqual(rc, cmd.ERROR)


@mock.patch("projects.tasks.check_build_status", mock.MagicMock(return_value=None))
@mock.patch("projects.models.build_code_to_docker", mock.MagicMock(return_value=(True, "Task_id")))
@mock.patch("api.views.execute.release_deploy", mock.MagicMock(return_value=None))
class ReleasesCmdTest(TestCase):

    def setUp(self):
        self.user = CustomUserFactory()
        self.project = ProjectFactory(user=self.user)

    def test_releases_create(self):
        cmd = ReleasesCmd(self.user)

        rc, out, err = cmd.run(u"create -p {0} tag".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create --project={0} tag".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create")
        self.assertEqual(rc, cmd.ERROR)

    def test_releases_force(self):
        cmd = ReleasesCmd(self.user)
        rc, out, err = cmd.run(u"create -p {0} tag --force".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create -p {0} tag -f".format(self.project.name))
        self.assertEqual(rc, cmd.OK)

    def test_releases_list(self):
        cmd = ReleasesCmd(self.user)
        cmd.run(u"create --project {0} mc9@#U@JHC@".format(self.project.name))
        ProjectReleaseFactory.create_batch(5)

        rc, out, err = cmd.run(u'list -p {0}'.format(self.project.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u'list')
        self.assertEqual(rc, cmd.ERROR)

    def test_releases_create_build(self):
        user = CustomUserFactory()
        project = ProjectFactory(user=user)
        cmd = ReleasesCmd(user)

        with mock.patch("projects.models.build_code_to_docker", mock.MagicMock(return_value=(False, "Error"))):
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.OK)

            Project.objects.update(git_repo="")
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.ERROR)

            ProjectBuild.objects.update(status=ProjectBuild.STATUS.Finished)
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.OK)

        with mock.patch("projects.models.build_code_to_docker", mock.MagicMock(return_value=(True, "Task_id"))):
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.OK)

            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@ --no-build".format(project.name))
            self.assertEqual(rc, cmd.OK)

            ProjectBuild.objects.update(status=ProjectBuild.STATUS.Finished)
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.OK)

            Project.objects.update(git_id_rsa="")
            ProjectBuild.objects.update(status=ProjectBuild.STATUS.Failed)
            rc, out, err = cmd.run(u"create --project {0} mc9@#U@JHC@".format(project.name))
            self.assertEqual(rc, cmd.ERROR)


@mock.patch("addons.models.get_cinder", mock.MagicMock(return_value=None))
class SnapshotsCmdTest(TestCase):

    def test_snapshots_create(self):

        user = CustomUserFactory()
        addon = AddonMemcachedFactory(user=user)
        cmd = SnapshotsCmd(user)
        rc, out, err = cmd.run(u"create -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.ERROR)

        addon = AddonMySQLFactory(user=user)
        rc, out, err = cmd.run(u"create -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.OK)

    def test_snapshots_description_create(self):

        user = CustomUserFactory()
        addon = AddonMySQLFactory(user=user)
        cmd = SnapshotsCmd(user)

        rc, out, err = cmd.run(u"create -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create -a {0} test".format(addon.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create -a {0} 测试".format(addon.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"create -a {0} 'just s test'".format(addon.name))
        self.assertEqual(rc, cmd.OK)

    def test_snapshots_destroy(self):
        user = CustomUserFactory()
        addon = AddonMySQLFactory(user=user)
        cmd = SnapshotsCmd(user)

        cmd.run(u"create -a {0}".format(addon.name))
        self.assertEqual(addon.snapshots.count(), 1)

        snapshot_id = addon.snapshots.all()[0].short_id
        rc, out, err = cmd.run(u"destroy -a {0} {1}".format(addon.name, snapshot_id))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"destroy -a {0} {1}".format(addon.name, 'notfound'))
        self.assertEqual(rc, cmd.ERROR)

    def test_snapshots_list(self):
        user = CustomUserFactory()
        addon = AddonMySQLFactory(user=user)
        cmd = SnapshotsCmd(user)

        cmd.run(u"create -a {0}".format(addon.name))
        cmd.run(u"create -a {0}".format(addon.name))
        cmd.run(u"create -a {0}".format(addon.name))
        snapshots = AddonSnapshot.objects.filter(addon=addon).all()
        self.assertEqual(snapshots.count(), 3)

        rc, out, err = cmd.run(u"list -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"list -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.OK)


@mock.patch("addons.models.get_cinder", mock.MagicMock(return_value=None))
@mock.patch("projects.tasks.check_build_status", mock.MagicMock(return_value=None))
@mock.patch("projects.models.build_code_to_docker", mock.MagicMock(return_value=(True, "Task_id")))
@mock.patch("api.views.execute.create_or_update_marathon_app", mock.MagicMock(return_value=None))
@mock.patch("api.views.execute.destroy_marathon_app", mock.MagicMock(return_value=None))
@mock.patch("api.views.execute.release_deploy", mock.MagicMock(return_value=None))
@mock.patch("api.views.execute.create_volume_and_release", mock.MagicMock(return_value=None))
class xxxxxCmdTest(TestCase):

    def test_project_cmd(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"projects create")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        rc, out, err = cmd.run(u"projects create foo")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 2)
        self.assertTrue(Project.objects.filter(name=u"foo").exists())

        rc, out, err = cmd.run(u'projects info foo')
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"projects destroy foo")
        self.assertEqual(rc, cmd.OK)
        self.assertFalse(Project.objects.filter(name=u"foo").exists())

        rc, out, err = cmd.run(u'projects info foo')
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u'projects list')
        self.assertEqual(rc, cmd.OK)

    def test_config_cmd(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"config set -p foo key=value")
        self.assertEqual(rc, cmd.ERROR)

        cmd.run(u"projects create foo")
        rc, out, err = cmd.run(u"config set -p foo key=value")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"config get -p foo key")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(out, u"value")

        rc, out, err = cmd.run(u"config list -p foo")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"config unset -p foo key")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"config list -p foo")
        self.assertEqual(rc, cmd.OK)

    def test_addons_cmd(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)
        project = ProjectFactory(name=u"foo", user=user)

        rc, out, err = cmd.run(u"addons create -p foo")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons create -p foo mysql --name my-foo")
        self.assertEqual(rc, cmd.OK)
        mysql = AddonMySQL.objects.all()
        self.assertEqual(mysql.count(), 1)
        mysql = mysql[0]
        self.assertEqual(mysql.name, u"my-foo")

        rc, out, err = cmd.run(u"addons create -p foo mysql -a base_url")
        self.assertEqual(rc, cmd.OK)
        self.assertIn(u"BASE_URL", project.get_configs().keys())

        rc, out, err = cmd.run(u"addons create -p foo mysql -a bar --name bar")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"addons create -p foo mysql --as bar1 --name foo")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"addons create -p foo mysql --as bar --name foo")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons destroy foo")
        self.assertEqual(rc, cmd.OK)

        project = ProjectFactory(name=u"test", user=user)
        rc, out, err = cmd.run(u"addons attach my-foo -p test --as bar")
        self.assertEqual(rc, cmd.OK)
        self.assertIn(u"BAR", project.get_configs().keys())

        project = ProjectFactory(user=user)
        rc, out, err = cmd.run(u"addons create mysql --name my-scale -p {0}".format(project.name))
        self.assertEqual(rc, cmd.OK)
        rc, out, err = cmd.run(u"addons scale my-scale -c 2")
        self.assertEqual(rc, cmd.OK)

        addon = Addon.objects.get(name='my-scale')
        self.assertEqual(addon.cpus, 2)

    def test_snapshots_cmd(self):
        user = CustomUserFactory()
        addon = AddonFactory(user=user)
        psql = AddonPostgresqlFactory(user=user)
        redis = AddonRedisFactory(user=user)
        memcached = AddonMemcachedFactory(user=user)
        mongodb = AddonMongodbFactory(user=user)
        rabbitmq = AddonRabbitmqFactory(user=user)
        mysql = AddonMySQLFactory(user=user)
        influxdb = AddonInfluxdbFactory(user=user)
        statsd = AddonStatsdFactory(user=user)
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(addon.name))
        self.assertEqual(rc, cmd.ERROR)
        snapshots = AddonSnapshot.objects.filter(addon=addon)
        self.assertEqual(snapshots.count(), 0)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(memcached.name))
        self.assertEqual(rc, cmd.ERROR)
        snapshots = AddonSnapshot.objects.filter(addon=memcached)
        self.assertEqual(snapshots.count(), 0)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(statsd.name))
        self.assertEqual(rc, cmd.ERROR)
        snapshots = AddonSnapshot.objects.filter(addon=statsd)
        self.assertEqual(snapshots.count(), 0)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(rabbitmq.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=rabbitmq)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(influxdb.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=influxdb)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(mongodb.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=mongodb)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(redis.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=redis)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(psql.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=psql)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[0].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0}".format(mysql.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=mysql)
        self.assertEqual(snapshots.count(), 1)
        self.assertEqual(snapshots[snapshots.count() - 1].short_id, 1)

        rc, out, err = cmd.run(u"snapshots create -a {0} test".format(mysql.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=mysql).order_by("short_id")
        self.assertEqual(snapshots.count(), 2)
        self.assertEqual(snapshots[snapshots.count() - 1].short_id, 2)

        rc, out, err = cmd.run(u"snapshots create -a {0} 测试".format(mysql.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=mysql).order_by("short_id")
        self.assertEqual(snapshots.count(), 3)
        self.assertEqual(snapshots[snapshots.count() - 1].short_id, 3)

        rc, out, err = cmd.run(u"snapshots create -a {0} just a test for snapshot".format(mysql.name))
        self.assertEqual(rc, cmd.OK)
        snapshots = AddonSnapshot.objects.filter(addon=mysql).order_by("short_id")
        self.assertEqual(snapshots.count(), 4)
        self.assertEqual(snapshots[snapshots.count() - 1].short_id, 4)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(addon.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(statsd.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(memcached.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(rabbitmq.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(influxdb.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(mongodb.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(redis.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(psql.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(mysql.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots destroy -a {0} 1".format(rabbitmq.name))
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"snapshots list -a {0}".format(rabbitmq.name))
        self.assertEqual(rc, cmd.OK)

    def test_releases_cmd(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)
        project = ProjectFactory(name=u"foo", user=user)

        rc, out, err = cmd.run(u"releases create -p {0}".format(project.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"releases create")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"releases create -p={0}".format(project.name))
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"releases tag")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"releases create tag")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"releases create -p {0} tag".format(project.name))
        self.assertEqual(rc, cmd.OK)

    def test_validate_name(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"projects create #test")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create 9uf993")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create test_mine")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create test-mine")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        rc, out, err = cmd.run(u"addons create redis -p test-mine -n #addon-mysql")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create redis -p test-mine -n addon_mysql")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create redis -p test-mine -n 9addon-mysql")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create redis -p test-mine -n addon-mysql")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.all().count(), 1)

    def test_validate_cpus(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"projects create -c foo project")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -c 0 project")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -c 9 project")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -c 4 project")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        rc, out, err = cmd.run(u"projects scale project -c one")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale project -c 0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale project -c 9")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale project -c 6")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="project")
        self.assertEqual(project.cpus, 6)

        rc, out, err = cmd.run(u"addons create elasticsearch -p project -c two -n es")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create elasticsearch -p project -c 0 -n es")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create elasticsearch -p project -c 9 -n es")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create elasticsearch -p project -c 7 -n es")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.all().count(), 1)

        rc, out, err = cmd.run(u"addons scale es -c five")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale es -c 0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale es -c 9")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale es -c 8")
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.get(name="es")
        self.assertEqual(addon.cpus, 8)

    def test_validate_mem(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"projects create -m mem")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -m 0")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -m 20000")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -m 10000")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        cmd.run(u"projects create test")
        rc, out, err = cmd.run(u"projects scale test -m three")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -m 0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -m 99999")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -m xxx")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -m 4096")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="test")
        self.assertEqual(project.mem, 4096)

        rc, out, err = cmd.run(u"addons create -p test rabbitmq -m mem -n rabbitmq -a base_url")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create -p test rabbitmq -m 0 -n rabbitmq -a base_url")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create -p test rabbitmq -m 17000 -n rabbitmq -a base_url")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create -p test rabbitmq -m ### -n rabbitmq -a base_url")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Addon.objects.all().count(), 0)

        rc, out, err = cmd.run(u"addons create -p test rabbitmq -m 9999 -n rabbitmq -a base_url")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Addon.objects.all().count(), 1)

        rc, out, err = cmd.run(u"addons scale rabbitmq -m one-thousand")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale rabbitmq -m 0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale rabbitmq -m 20000")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale rabbitmq -m xxx")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"addons scale rabbitmq -m 10240")
        self.assertEqual(rc, cmd.OK)
        addon = Addon.objects.get(name="rabbitmq")
        self.assertEqual(addon.mem, 10240)

    def test_validate_instances(self):

        user = CustomUserFactory()
        cmd = xxxxxCmd(user)

        rc, out, err = cmd.run(u"projects create -i instances")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -i 0")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -i -20")
        self.assertEqual(rc, cmd.ERROR)
        self.assertEqual(Project.objects.all().count(), 0)

        rc, out, err = cmd.run(u"projects create -i 10")
        self.assertEqual(rc, cmd.OK)
        self.assertEqual(Project.objects.all().count(), 1)

        cmd.run(u"projects create test")
        rc, out, err = cmd.run(u"projects scale test -i three")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -i 0")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -i 99999")
        self.assertEqual(rc, cmd.OK)

        rc, out, err = cmd.run(u"projects scale test -i xxx")
        self.assertEqual(rc, cmd.ERROR)

        rc, out, err = cmd.run(u"projects scale test -i 46")
        self.assertEqual(rc, cmd.OK)
        project = Project.objects.get(name="test")
        self.assertEqual(project.instances, 46)
