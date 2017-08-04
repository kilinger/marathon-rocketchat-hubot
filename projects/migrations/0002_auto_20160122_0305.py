# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectport',
            name='host_port',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='projectport',
            name='protocol',
            field=models.CharField(default=b'tcp', max_length=3, choices=[(b'tcp', 'TCP'), (b'udp', 'UDP')]),
        ),
        migrations.AddField(
            model_name='projectport',
            name='service_port',
            field=models.IntegerField(default=0),
        ),
    ]
