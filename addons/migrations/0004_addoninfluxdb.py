# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0003_addonmongodb'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddonInfluxdb',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
                ('db_name', hubot.fields.RandomCharField(include_digits=False, length=6, max_length=32, lowercase=True, blank=True)),
                ('db_user', hubot.fields.RandomCharField(include_digits=False, length=8, max_length=8, lowercase=True, blank=True)),
                ('db_password', hubot.fields.RandomCharField(length=16, max_length=16, blank=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
    ]
