# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0008_addonsnapshot'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='addonsnapshot',
            options={'verbose_name': 'Addon Snapshot'},
        ),
        migrations.AddField(
            model_name='addon',
            name='deployment_id',
            field=models.CharField(max_length=128, verbose_name='Marathon Deployment Id', blank=True),
        ),
        migrations.AddField(
            model_name='addon',
            name='m_version',
            field=models.CharField(max_length=128, verbose_name='Marathon Version', blank=True),
        ),
        migrations.AddField(
            model_name='addon',
            name='status',
            field=model_utils.fields.StatusField(default=b'Staging', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(0, 'dummy')]),
        ),
        migrations.AddField(
            model_name='addon',
            name='status_changed',
            field=model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status'),
        ),
    ]
