# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0005_addon_depend'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddonStatsd',
            fields=[
                ('addon_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='addons.Addon')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('addons.addon',),
        ),
    ]
