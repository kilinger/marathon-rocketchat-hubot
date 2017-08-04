# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import hubot.utils.mesos
import hubot.fields


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('cpus', models.FloatField()),
                ('mem', models.FloatField()),
                ('instances', models.IntegerField(default=1)),
                ('name', models.CharField(max_length=128)),
                ('namespace', models.CharField(max_length=32)),
                ('git_repo', models.CharField(help_text='The git repository to clone and build', max_length=512, blank=True)),
                ('git_id_rsa', models.TextField(help_text='The private SSH key to use when cloning the git repository', blank=True)),
                ('health_check', models.CharField(default=b'/', max_length=512, blank=True)),
                ('domain', models.CharField(max_length=200, blank=True)),
                ('image_name', models.CharField(max_length=100, blank=True)),
            ],
            options={
                'verbose_name': 'Project',
            },
        ),
        migrations.CreateModel(
            name='ProjectAddon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('alias', models.CharField(max_length=64, blank=True)),
                ('primary', models.BooleanField(default=False)),
                ('addon', models.ForeignKey(to='addons.Addon')),
                ('project', models.ForeignKey(to='projects.Project')),
            ],
            options={
                'ordering': ('modified', 'created'),
            },
        ),
        migrations.CreateModel(
            name='ProjectBuild',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'Success', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'Success', b'Success'), (b'Failed', b'Failed'), (b'Cancel', b'Cancel')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('git_tag', models.CharField(default=b'master', max_length=512, blank=True)),
                ('project', models.ForeignKey(related_name='builds', to='projects.Project')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'verbose_name': 'Project Build',
            },
        ),
        migrations.CreateModel(
            name='ProjectConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('key', hubot.fields.UpperCaseCharField(max_length=64, verbose_name='Key')),
                ('value', models.CharField(max_length=128, verbose_name='Value')),
                ('project', models.ForeignKey(related_name='configs', to='projects.Project')),
            ],
            options={
                'ordering': ('key', 'created'),
                'verbose_name': 'Config',
            },
        ),
        migrations.CreateModel(
            name='ProjectPort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('port', models.CharField(max_length=512)),
                ('project', models.ForeignKey(related_name='ports', to='projects.Project')),
            ],
            options={
                'verbose_name': 'Project Port',
            },
        ),
        migrations.CreateModel(
            name='ProjectRelease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'Success', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'Success', b'Success'), (b'Failed', b'Failed'), (b'Cancel', b'Cancel')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('build', models.ForeignKey(related_name='deploys', to='projects.ProjectBuild')),
                ('project', models.ForeignKey(related_name='deployments', editable=False, to='projects.Project')),
            ],
            options={
                'ordering': ('-modified',),
                'verbose_name': 'Release',
            },
            bases=(hubot.utils.mesos.MarathonAppMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ProjectVolume',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('container_path', models.CharField(max_length=512)),
                ('is_block_volume', models.BooleanField(default=False)),
                ('project', models.ForeignKey(related_name='volumes', to='projects.Project')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='addons',
            field=models.ManyToManyField(related_name='projects', through='projects.ProjectAddon', to='addons.Addon'),
        ),
        migrations.AddField(
            model_name='project',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='projectport',
            unique_together=set([('project', 'port')]),
        ),
        migrations.AlterUniqueTogether(
            name='projectconfig',
            unique_together=set([('project', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='projectaddon',
            unique_together=set([('project', 'addon')]),
        ),
        migrations.AlterUniqueTogether(
            name='project',
            unique_together=set([('namespace', 'name')]),
        ),
    ]
