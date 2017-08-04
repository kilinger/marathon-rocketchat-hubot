# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0013_auto_20160405_1804'),
    ]

    operations = [
        migrations.AddField(
            model_name='addon',
            name='backup_enable',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='addon',
            name='backup_hour',
            field=models.IntegerField(default=0, verbose_name='Execute task Hour', validators=[hubot.models.validate_hour]),
        ),
        migrations.AddField(
            model_name='addon',
            name='backup_keep',
            field=models.IntegerField(default=7, help_text='Snapshots number to keep', validators=[hubot.models.validate_backup_keep]),
        ),
        migrations.AddField(
            model_name='addon',
            name='backup_minute',
            field=models.IntegerField(default=0, verbose_name='Execute task Minute', validators=[hubot.models.validate_minute]),
        ),
    ]
