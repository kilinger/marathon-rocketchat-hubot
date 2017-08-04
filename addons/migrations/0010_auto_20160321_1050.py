# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0009_auto_20160305_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='addon',
            name='volume_ids',
            field=models.TextField(verbose_name='OpenStack Volume Ids', blank=True),
        ),
        migrations.AddField(
            model_name='addon',
            name='volume_size',
            field=models.IntegerField(default=16, verbose_name='OpenStack Volume Size'),
            preserve_default=False,
        ),
    ]
