# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_auto_20160311_1757'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectrelease',
            options={'ordering': ('-modified',), 'verbose_name': 'Project Release'},
        ),
    ]
