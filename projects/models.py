# -*- coding:utf-8 -*-
import logging
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices, FieldTracker
from hubot.utils.build import build_code_to_docker

from hubot.fields import UpperCaseCharField
from hubot.models import MesosResourceModel, NamespaceModel
from hubot.utils.mesos import MarathonAppMixin, clean_container_path


logger = logging.getLogger('hubot')


@python_2_unicode_compatible
class Project(NamespaceModel, MesosResourceModel):

    git_repo = models.CharField(max_length=512, help_text=_(u"The git repository to clone and build"), blank=True)
    git_id_rsa = models.TextField(help_text=_(u"The private SSH key to use when cloning the git repository"),
                                  blank=True)

    health_check = models.CharField(max_length=512, default='/', blank=True)

    domain = models.CharField(max_length=200, blank=True)

    image_name = models.CharField(max_length=100, blank=True)

    args = models.CharField(max_length=500, blank=True)

    redirect_https = models.BooleanField(default=False)
    use_hsts = models.BooleanField(default=False)
    use_lb = models.BooleanField(default=True, help_text=_(u"enable marathon-lb"))

    addons = models.ManyToManyField('addons.Addon', through='projects.ProjectAddon', related_name='projects')

    tracker = FieldTracker()

    class Meta:
        verbose_name = _(u"Project")
        unique_together = (("namespace", "name"),)

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return self.full_name(namespace_first=False)

    @property
    def host(self):
        return u"{0}.{1}".format(self.slug, settings.HUBOT_DOMAIN)

    def get_weave_cidr(self):
        return self.user.subnet

    def create_release(self, tag):
        """
        :rtype: `projects.models.ProjectRelease`
        """
        build, create = ProjectBuild.objects.get_or_create(project=self, tag=tag)
        return ProjectRelease.objects.get_or_create(build=build)[0]

    def get_configs(self):
        """
        :return dict
        """
        configs = dict((e.key.upper(), e.value) for e in self.configs.all())

        for pa in ProjectAddon.objects.filter(project=self).all():
            addon = getattr(pa.addon, "addon" + pa.addon.slug)
            configs.update(addon.get_config(primary=pa.primary, alias=pa.alias))

        return configs

    def get_ports(self):
        return list((p.container_port, p.host_port, p.service_port, p.protocol) for p in self.ports.all())

    def get_host(self):
        return self.host

    @property
    def vhost(self):
        return self.domain + "," + self.host if self.domain else self.host

    def get_running_release(self):
        try:
            release = ProjectRelease.objects.filter(project=self,
                                                    status=ProjectRelease.STATUS.Running).order_by("-modified")[0]
        except Exception as e:
            logger.error(str(e))
            release = None
        return release


@receiver(post_save, sender=Project, dispatch_uid='on_project_save')
def on_project_save(sender, instance, created, **kwargs):
    if created:
        ProjectPort.objects.get_or_create(project=instance, port=5000, container_port=5000)


@python_2_unicode_compatible
class ProjectVolume(models.Model):

    MODE = Choices(
        ('RW', _(u'读写')),
        ('RO', _(u'只写')),
    )

    project = models.ForeignKey(Project, related_name=_('volumes'))
    container_path = models.CharField(max_length=512)
    host_path = models.CharField(max_length=512, blank=True)
    is_block_volume = models.BooleanField(default=False)
    mode = models.CharField(max_length=2, choices=MODE, default=MODE.RW)

    def __str__(self):
        return "{0}({1})".format(self.project, self.container_path)


@python_2_unicode_compatible
class ProjectPort(models.Model):
    PROTOCOL = Choices(
        ('tcp', 'TCP', _(u"TCP")),
        ('udp', 'UDP', _(u"UDP"))
    )

    project = models.ForeignKey(Project, related_name=_('ports'))
    port = models.CharField(max_length=512)
    container_port = models.IntegerField()
    host_port = models.IntegerField(default=0)
    service_port = models.IntegerField(default=0)
    protocol = models.CharField(max_length=3, choices=PROTOCOL, default=PROTOCOL.TCP)

    class Meta:
        verbose_name = _(u"Project Port")
        unique_together = (("project", "port"),)

    def __str__(self):
        return "{0}:{1}".format(self.project.name, self.port)


@python_2_unicode_compatible
class ProjectBuild(StatusModel, TimeStampedModel, models.Model):
    STATUS = Choices(
        ('Staging', _(u'准备打包')),
        ('Finished', _(u'打包成功')),
        ('Failed', _(u'打包失败'))
    )

    project = models.ForeignKey(Project, related_name=_('builds'))
    tag = models.CharField(max_length=512, default='master', blank=True)
    task_id = models.CharField(max_length=512, blank=True)

    class Meta:
        verbose_name = _(u"Project Build")
        ordering = ('-modified', '-created')

    def __str__(self):
        return "{0}:{1}".format(self.project.name, self.tag)

    def build(self):
        pass

    def is_success(self):
        return self.status == self.STATUS.Finished

    def do_build(self, image_name):
        git_repo = self.project.git_repo
        git_tag = self.tag
        git_id_rsa = self.project.git_id_rsa if self.project.git_id_rsa else self.project.user.git_id_rsa
        state, task_id = build_code_to_docker(image_name, git_repo, git_tag, git_id_rsa)
        if state:
            self.task_id = task_id
            self.status = ProjectBuild.STATUS.Staging
            self.save()
            from projects.tasks import check_build_status
            check_build_status.apply_async(args=[task_id], countdown=settings.TIMEOUT_FOR_STATUS_FINISHED)


@python_2_unicode_compatible
class ProjectConfig(TimeStampedModel, models.Model):
    project = models.ForeignKey(Project, related_name=_(u'configs'))
    key = UpperCaseCharField(max_length=255, verbose_name=_(u'Key'))
    value = models.CharField(max_length=1000, verbose_name=_(u'Value'))

    class Meta:
        verbose_name = _(u"Config")
        ordering = ('key', 'created',)
        unique_together = (("project", "key"),)

    def __str__(self):
        return "{0}:{1}".format(self.project.name, self.key)


@python_2_unicode_compatible
class ProjectRelease(MarathonAppMixin, StatusModel, TimeStampedModel, models.Model):

    STATUS = Choices(
        ('Building', _(u'打包中')),
        ('Staging', _(u'部署中')),
        ('Running', _(u'运行中')),
        ('Suspend', _(u'已暂停')),
        ('Failed', _(u'部署失败')),
        ('Finished', _(u'已结束'))
    )

    project = models.ForeignKey(Project, related_name=_('releases'), editable=False)
    build = models.ForeignKey(ProjectBuild, related_name=_('deploys'))
    m_version = models.CharField(max_length=128, blank=True, verbose_name=_('Marathon Version'))
    deployment_id = models.CharField(max_length=128, blank=True, verbose_name=_('Marathon Deployment Id'))

    class Meta:
        verbose_name = _(u"Project Release")
        ordering = ('-modified',)

    def __str__(self):
        return u"{0}:{1}".format(self.project.name, self.build.tag)

    def mark_failed(self):
        self.status = self.STATUS.Failed
        self.save()

    def check_status_after(self, seconds):
        from hubot.tasks import check_release_status
        check_release_status.apply_async(args=[self.deployment_id], countdown=seconds)

    def check_suspend(self):
        from hubot.tasks import check_release_suspend
        check_release_suspend.apply_async(args=[self.build.tag])

    def do_rollback(self):
        if self.deployment_id:
            from hubot.utils.mesos import marathon
            try:
                app = marathon.delete_deployment(self.deployment_id)
            except Exception as e:
                logger.error(str(e))
            else:
                try:
                    release = ProjectRelease.objects.filter(project=self.project, status=ProjectRelease.STATUS.Running
                                                            ).order_by("-modified")[0]
                except Exception as e:
                    logger.error(str(e))
                else:
                    release.m_version = app['version']
                    release.deployment_id = app['deploymentId']
                    release.save()
                    from hubot.tasks import check_release_status
                    check_release_status.apply_async(args=[release.deployment_id],
                                                     countdown=settings.TIMEOUT_FOR_STATUS_FINISHED)

    @property
    def marathon_app_id(self):
        return self.project.slug

    @property
    def force_pull_image(self):
        return True

    def get_marathon_app_id(self):
        return self.marathon_app_id

    def get_args(self):
        if self.project.args:
            return self.project.args.split()

    @property
    def container_paths(self):
        return [pv for pv in ProjectVolume.objects.filter(project=self.project, is_block_volume=False)]

    @property
    def docker_parameters(self):
        parameters = [dict(key="label", value="weave_hostname={0}".format(self.project.slug + "-app"))]

        volumes = ProjectVolume.objects.filter(project=self.project, is_block_volume=True)
        if volumes:
            parameters.append(dict(key="volume-driver", value="rexray"))
            for volume in volumes:
                value = "{0}-{1}:{2}".format(self.get_marathon_app_id(),
                                             clean_container_path(volume.container_path), volume.container_path)
                parameters.append(dict(key="volume", value=value))

        return parameters

    def get_env(self):
        configs = self.project.get_configs()
        configs.update({'WEAVE_CIDR': self.project.get_weave_cidr(), 'APP_VERSION': self.build.tag})
        return configs

    def get_labels(self):
        labels = {}
        if self.project.use_lb:
            labels.update(**{"HAPROXY_GROUP": "external", "HAPROXY_0_VHOST": self.project.vhost})
            if self.project.redirect_https:
                labels.update(**{"HAPROXY_0_REDIRECT_TO_HTTPS": "true"})
            if self.project.use_hsts:
                labels.update(**{"HAPROXY_0_USE_HSTS": "true"})
        return labels

    def get_mem(self):
        return self.project.mem

    def get_instances(self):
        return self.project.instances

    def get_cpus(self):
        return self.project.cpus

    def get_container_image(self):
        if self.project.image_name:
            image_name = self.project.image_name
        else:
            image_name = "{0}/{1}".format(self.project.namespace, self.project.name)
        return "{0}:{1}".format(image_name, self.build.tag)

    def get_ports(self):
        return self.project.get_ports()

    def get_health_checks(self):
        from marathon.models import MarathonHealthCheck
        checks = []
        if self.project.health_check:
            checks = [MarathonHealthCheck(port_index=0, path=self.project.health_check)]
        return checks

    def get_upgrade_strategy(self):
        return dict(minimum_health_capacity=settings.MINIMUM_HEALTH_CAPACITY)

    def save(self, *args, **kwargs):
        self.project = self.build.project
        super(ProjectRelease, self).save(*args, **kwargs)


@python_2_unicode_compatible
class ProjectAddon(TimeStampedModel, models.Model):
    project = models.ForeignKey(Project)
    addon = models.ForeignKey("addons.Addon")
    alias = models.CharField(max_length=64, blank=True)
    primary = models.BooleanField(default=False)

    class Meta:
        ordering = ('modified', 'created',)
        unique_together = (("project", "addon"),)

    def __str__(self):
        return u"{0}:{1}".format(self.project.name, self.addon)


@receiver(post_save, sender=ProjectAddon)
def update_project_addon_primary(sender, instance=None, created=False, **kwargs):
    if created:
        if not ProjectAddon.objects.filter(project=instance.project,
                                           addon__slug=instance.addon.slug).exclude(id=instance.id).exists():
            ProjectAddon.objects.filter(id=instance.id).update(primary=True)
