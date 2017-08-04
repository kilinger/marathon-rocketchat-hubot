# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_auto_20160122_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='cpus',
            field=models.FloatField(validators=[hubot.models.validate_cpus]),
        ),
        migrations.AlterField(
            model_name='project',
            name='mem',
            field=models.FloatField(validators=[hubot.models.validate_mem]),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=128, validators=[hubot.models.validate_name]),
        ),
    ]
