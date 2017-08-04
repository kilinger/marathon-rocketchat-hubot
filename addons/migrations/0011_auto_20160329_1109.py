# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0010_auto_20160321_1050'),
    ]

    operations = [
        migrations.AddField(
            model_name='addonsnapshot',
            name='volume_ids',
            field=models.TextField(verbose_name='Restore Volume Ids', blank=True),
        ),
        migrations.AlterField(
            model_name='addon',
            name='volume_size',
            field=models.IntegerField(verbose_name='OpenStack Volume Size', validators=[hubot.models.validate_size]),
        ),
    ]
