# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0007_auto_20160128_1546'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddonSnapshot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('short_id', models.IntegerField(default=0)),
                ('snapshot_ids', models.TextField(blank=True)),
                ('description', models.CharField(max_length=1000, blank=True)),
                ('addon', models.ForeignKey(related_name='snapshots', to='addons.Addon')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
