# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20160317_0943'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='use_hsts',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='project',
            name='redirect_https',
            field=models.BooleanField(default=False),
        ),
    ]
