# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20160201_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='git_id_rsa',
            field=models.TextField(help_text='The private SSH key to use when cloning the git repository', verbose_name='SSH\u79c1\u94a5', blank=True),
        ),
    ]
