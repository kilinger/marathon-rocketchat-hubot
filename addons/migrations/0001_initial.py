# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import addons.mixins
import hubot.fields
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import hubot.utils.mesos
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Addon',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('cpus', models.FloatField()),
                ('mem', models.FloatField()),
                ('instances', models.IntegerField(default=1)),
                ('name', models.CharField(max_length=128)),
                ('namespace', models.CharField(max_length=32)),
                ('deleted', models.BooleanField(default=False)),
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('color', models.CharField(max_length=128, verbose_name='\u989c\u8272\u6807\u8bc6', blank=True)),
                ('slug', models.CharField(max_length=64)),
                ('version', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name': 'Addon',
            },
            bases=(addons.mixins.AddonsMixin, hubot.utils.mesos.MarathonAppMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AddonElasticSearch',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.CreateModel(
            name='AddonMemcached',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.CreateModel(
            name='AddonMySQL',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
                ('db_name', hubot.fields.RandomCharField(length=6, include_digits=False, editable=False, lowercase=True, blank=True)),
                ('db_user', hubot.fields.RandomCharField(length=8, include_digits=False, editable=False, lowercase=True, blank=True)),
                ('db_password', hubot.fields.RandomCharField(length=16, editable=False, blank=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.CreateModel(
            name='AddonPostgresql',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
                ('db_name', hubot.fields.RandomCharField(length=6, include_digits=False, editable=False, lowercase=True, blank=True)),
                ('db_user', hubot.fields.RandomCharField(length=8, include_digits=False, editable=False, lowercase=True, blank=True)),
                ('db_password', hubot.fields.RandomCharField(length=16, editable=False, blank=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.CreateModel(
            name='AddonRabbitmq',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
                ('mq_user', hubot.fields.RandomCharField(length=8, include_digits=False, editable=False, lowercase=True, blank=True)),
                ('mq_password', hubot.fields.RandomCharField(length=16, editable=False, blank=True)),
                ('mq_vhost', hubot.fields.RandomCharField(length=6, include_digits=False, editable=False, lowercase=True, blank=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.CreateModel(
            name='AddonRedis',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
        migrations.AddField(
            model_name='addon',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
