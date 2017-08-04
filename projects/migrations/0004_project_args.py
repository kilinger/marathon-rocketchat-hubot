# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_projectport_container_port'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='args',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
