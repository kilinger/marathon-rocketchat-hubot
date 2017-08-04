# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0006_addonstatsd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addon',
            name='cpus',
            field=models.FloatField(validators=[hubot.models.validate_cpus]),
        ),
        migrations.AlterField(
            model_name='addon',
            name='mem',
            field=models.FloatField(validators=[hubot.models.validate_mem]),
        ),
        migrations.AlterField(
            model_name='addon',
            name='name',
            field=models.CharField(max_length=128, validators=[hubot.models.validate_name]),
        ),
    ]
