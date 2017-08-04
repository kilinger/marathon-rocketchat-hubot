# -*- coding: utf-8 -*-
from django.test import TestCase
from addons.factories import AddonMySQLFactory, AddonRabbitmqFactory, AddonMemcachedFactory


class AddonMySQLTest(TestCase):

    def test_get_config(self):
        addon = AddonMySQLFactory()

        config = addon.get_config(primary=True)
        for var in addon.get_config_vars():
            self.assertTrue(var in config)

    def test_resource(self):
        mem = 1024
        cpus = 2
        instances = 3
        addon = AddonMySQLFactory(mem=mem, cpus=cpus, instances=instances)
        self.assertEqual(addon.get_mem(), mem)
        self.assertEqual(addon.get_cpus(), cpus)
        self.assertEqual(addon.get_instances(), instances)


class AddonRabbitmqTest(TestCase):

    def test_get_config(self):
        addon = AddonRabbitmqFactory()

        config = addon.get_config(primary=True)
        for var in addon.get_config_vars():
            self.assertTrue(var in config)


class SnapshotTest(TestCase):

    def test_snapshots_support(self):
        addon = AddonMySQLFactory()
        self.assertTrue(addon.has_snapshot_support())

        addon = AddonMemcachedFactory()
        self.assertFalse(addon.has_snapshot_support())
