# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_auto_20160310_1429'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectbuild',
            name='task_id',
            field=models.CharField(max_length=512, blank=True),
        ),
        migrations.AlterField(
            model_name='projectbuild',
            name='status',
            field=model_utils.fields.StatusField(default=b'Staging', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(0, 'dummy')]),
        ),
        migrations.AlterField(
            model_name='projectrelease',
            name='status',
            field=model_utils.fields.StatusField(default=b'Building', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(0, 'dummy')]),
        ),
    ]
