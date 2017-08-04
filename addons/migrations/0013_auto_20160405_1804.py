# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0012_addon_args'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='addonsnapshot',
            options={'ordering': ('-short_id', '-modified'), 'verbose_name': 'Addon Snapshot'},
        ),
    ]
