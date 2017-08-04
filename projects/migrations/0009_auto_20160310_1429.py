# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20160310_1222'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectvolume',
            name='host_path',
            field=models.CharField(max_length=512, blank=True),
        ),
        migrations.AddField(
            model_name='projectvolume',
            name='mode',
            field=models.CharField(default=b'RW', max_length=2, choices=[(b'RW', '\u8bfb\u5199'), (b'RO', '\u53ea\u5199')]),
        ),
    ]
