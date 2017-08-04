# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20160122_0305'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectport',
            name='container_port',
            field=models.IntegerField(default=5000),
            preserve_default=False,
        ),
    ]
