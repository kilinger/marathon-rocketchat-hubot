# -*- coding: utf-8 -*-
import factory
from accounts.factories import CustomUserFactory
from addons.models import AddonMySQL, Addon, AddonRabbitmq, AddonMemcached, AddonPostgresql, AddonRedis, \
    AddonElasticSearch, AddonMongodb, AddonInfluxdb, AddonStatsd


class AddonFactory(factory.DjangoModelFactory):

    user = factory.SubFactory(CustomUserFactory)
    cpus = factory.Sequence(lambda a: float(1))
    mem = factory.Sequence(lambda a: float(512))
    instances = factory.Sequence(lambda a: int(1))
    volume_size = factory.Sequence(lambda a: int(1))

    class Meta:
        model = Addon


class AddonMySQLFactory(AddonFactory):

    class Meta:
        model = AddonMySQL


class AddonPostgresqlFactory(AddonFactory):

    class Meta:
        model = AddonPostgresql


class AddonElasticSearchFactory(AddonFactory):

    class Meta:
        model = AddonElasticSearch


class AddonMongodbFactory(AddonFactory):

    class Meta:
        model = AddonMongodb


class AddonRabbitmqFactory(AddonFactory):

    class Meta:
        model = AddonRabbitmq


class AddonInfluxdbFactory(AddonFactory):

    class Meta:
        model = AddonInfluxdb


class AddonStatsdFactory(AddonFactory):

    class Meta:
        model = AddonStatsd


class AddonMemcachedFactory(AddonFactory):

    class Meta:
        model = AddonMemcached


class AddonRedisFactory(AddonFactory):

    class Meta:
        model = AddonRedis
