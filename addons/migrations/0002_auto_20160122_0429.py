# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addonmysql',
            name='db_name',
            field=hubot.fields.RandomCharField(include_digits=False, length=6, max_length=32, lowercase=True, blank=True),
        ),
        migrations.AlterField(
            model_name='addonmysql',
            name='db_password',
            field=hubot.fields.RandomCharField(length=16, max_length=16, blank=True),
        ),
        migrations.AlterField(
            model_name='addonmysql',
            name='db_user',
            field=hubot.fields.RandomCharField(include_digits=False, length=8, max_length=8, lowercase=True, blank=True),
        ),
        migrations.AlterField(
            model_name='addonpostgresql',
            name='db_name',
            field=hubot.fields.RandomCharField(include_digits=False, length=6, max_length=32, lowercase=True, blank=True),
        ),
        migrations.AlterField(
            model_name='addonpostgresql',
            name='db_password',
            field=hubot.fields.RandomCharField(length=16, max_length=16, blank=True),
        ),
        migrations.AlterField(
            model_name='addonpostgresql',
            name='db_user',
            field=hubot.fields.RandomCharField(include_digits=False, length=8, max_length=8, lowercase=True, blank=True),
        ),
        migrations.AlterField(
            model_name='addonrabbitmq',
            name='mq_password',
            field=hubot.fields.RandomCharField(length=16, max_length=16, blank=True),
        ),
        migrations.AlterField(
            model_name='addonrabbitmq',
            name='mq_user',
            field=hubot.fields.RandomCharField(include_digits=False, length=8, max_length=8, lowercase=True, blank=True),
        ),
        migrations.AlterField(
            model_name='addonrabbitmq',
            name='mq_vhost',
            field=hubot.fields.RandomCharField(include_digits=False, length=6, max_length=32, lowercase=True, blank=True),
        ),
    ]
