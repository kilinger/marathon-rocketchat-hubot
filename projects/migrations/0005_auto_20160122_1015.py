# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_project_args'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projectbuild',
            old_name='git_tag',
            new_name='tag',
        ),
    ]
