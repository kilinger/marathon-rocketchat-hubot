# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_auto_20160128_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectrelease',
            name='deployment_id',
            field=models.CharField(max_length=128, verbose_name='Marathon Deployment Id', blank=True),
        ),
        migrations.AddField(
            model_name='projectrelease',
            name='m_version',
            field=models.CharField(max_length=128, verbose_name='Marathon Version', blank=True),
        ),
        migrations.AlterField(
            model_name='projectrelease',
            name='project',
            field=models.ForeignKey(related_name='releases', editable=False, to='projects.Project'),
        ),
        migrations.AlterField(
            model_name='projectrelease',
            name='status',
            field=model_utils.fields.StatusField(default=b'Staging', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(0, 'dummy')]),
        ),
    ]
