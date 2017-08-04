# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0004_addoninfluxdb'),
    ]

    operations = [
        migrations.AddField(
            model_name='addon',
            name='depend',
            field=models.ForeignKey(blank=True, to='addons.Addon', null=True),
        ),
    ]
