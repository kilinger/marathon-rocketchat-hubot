# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import hubot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_auto_20160305_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectconfig',
            name='key',
            field=hubot.fields.UpperCaseCharField(max_length=255, verbose_name='Key'),
        ),
        migrations.AlterField(
            model_name='projectconfig',
            name='value',
            field=models.CharField(max_length=1000, verbose_name='Value'),
        ),
    ]
