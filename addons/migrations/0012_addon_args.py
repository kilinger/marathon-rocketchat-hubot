# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0011_auto_20160329_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='addon',
            name='args',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
