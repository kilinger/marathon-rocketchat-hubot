# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_auto_20160421_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='use_lb',
            field=models.BooleanField(default=True, help_text='enable'),
        ),
    ]
