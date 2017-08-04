# -*- coding: utf-8 -*-
import logging
import os.path

import time
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from marathon import MarathonApp, MarathonClient, MarathonHttpError
from marathon.models.container import MarathonContainerVolume, MarathonDockerContainer, MarathonContainer

LOG = logging.getLogger(__name__)


missing = object()


class MarathonAppMixin(object):

    DEFAULT_LABELS = {}
    DEFAULT_IMAGE = missing
    DEFAULT_FORCE_PULL_IMAGE = False
    DEFAULT_PORTS = []
    DEFAULT_NETWORK = 'BRIDGE'
    DEFAULT_ENV = {}

    DEFAULT_CPUS = 1
    DEFAULT_MEM = 128
    DEFAULT_INSTANCES = 1

    DEFAULT_CONSTRAINTS = [('node', 'LIKE', 'worker')]
    DEFAULT_URIS = ["file:///etc/docker.tar.gz"]
    DEFAULT_DEPENDENCIES = []

    def get_marathon_app_id(self):
        raise NotImplemented

    def get_args(self):
        args = getattr(self, 'args', [])
        if args:
            return args.split(",")
        return args

    def get_force_pull_image(self):
        return getattr(self, 'force_pull_image', self.DEFAULT_FORCE_PULL_IMAGE)

    def get_cpus(self):
        return getattr(self, 'cpus', self.DEFAULT_CPUS)

    def get_mem(self):
        return getattr(self, 'mem', self.DEFAULT_MEM)

    def get_instances(self):
        return getattr(self, 'instances', self.DEFAULT_INSTANCES)

    def get_env(self):
        return getattr(self, 'env', self.DEFAULT_ENV)

    def get_labels(self):
        return getattr(self, 'labels', self.DEFAULT_LABELS)

    def get_container_image(self):
        im = getattr(self, 'image', self.DEFAULT_IMAGE)
        if im is missing:
            raise Exception("image is required")
        return im

    def get_network(self):
        return getattr(self, 'network', self.DEFAULT_NETWORK)

    def get_ports(self):
        return getattr(self, 'ports', self.DEFAULT_PORTS)

    def get_port_mappings(self):
        port_mappings = []
        for port in self.get_ports():
            if isinstance(port, (tuple, list)):
                port_mapping = dict(container_port=port[0], host_port=port[1], service_port=port[2], protocol=port[3])
            else:
                try:
                    port = int(port)
                except ValueError:
                    continue
                else:
                    port_mapping = dict(container_port=port)
            port_mappings.append(port_mapping)
        return port_mappings

    def get_volumes(self):
        volumes = []
        container_paths = getattr(self, 'container_paths', [])
        for p in container_paths:
            if p.host_path:
                host_path = p.host_path
            else:
                host_path = os.path.join("/mnt/container-volumes/",
                                         self.get_marathon_app_id(), p.container_path.strip('/'))
            volumes.append(MarathonContainerVolume(container_path=p.container_path, host_path=host_path, mode=p.mode))
        return volumes

    def get_docker_parameters(self):
        return getattr(self, 'docker_parameters', {})

    def get_docker_container(self):
        docker = MarathonDockerContainer(image=get_image_fullname(self.get_container_image()),
                                         network=self.get_network(),
                                         force_pull_image=self.get_force_pull_image(),
                                         port_mappings=self.get_port_mappings(),
                                         parameters=self.get_docker_parameters())
        return MarathonContainer(docker=docker, volumes=self.get_volumes())

    def get_constraints(self):
        return getattr(self, 'constraints', self.DEFAULT_CONSTRAINTS)

    def get_dependencies(self):
        return getattr(self, 'dependencies', self.DEFAULT_DEPENDENCIES)

    def get_uris(self):
        return getattr(self, 'uris', self.DEFAULT_URIS)

    def get_upgrade_strategy(self):
        return getattr(self, 'upgrade_strategy', None)

    def get_health_checks(self):
        return getattr(self, 'health_checks', [])

    def get_marathon_app(self):

        env = self.get_env()
        for key, value in env.items():
            if isinstance(value, unicode):
                env[key] = value.encode('utf-8')

        return MarathonApp(args=self.get_args(),
                           container=self.get_docker_container(),
                           constraints=self.get_constraints(),
                           dependencies=self.get_dependencies(),
                           env=env,
                           uris=self.get_uris(),
                           labels=self.get_labels(),
                           cpus=self.get_cpus(),
                           mem=self.get_mem(),
                           instances=self.get_instances(),
                           upgrade_strategy=self.get_upgrade_strategy(),
                           health_checks=self.get_health_checks())


def create_or_update_marathon_app(obj, force=False):
    try:
        app = marathon.get_app(obj.marathon_app_id)
    except Exception as e:
        LOG.error(e)
        app = None
    if not app:
        app = marathon.create_app(obj.marathon_app_id, obj.get_marathon_app())
    else:
        app = marathon.update_app(obj.marathon_app_id, obj.get_marathon_app(), force=force)

    if hasattr(obj, "m_version") and hasattr(obj, "deployment_id"):
        from projects.models import ProjectRelease
        obj.status = ProjectRelease.STATUS.Staging
        if isinstance(app, dict):
            obj.m_version = app['version']
            obj.deployment_id = app['deploymentId']
        elif isinstance(app, MarathonApp):
            obj.m_version = app.version
            obj.deployment_id = app.deployments[0].id
        obj.save()
    if hasattr(obj, "check_status_after"):
        obj.check_status_after(settings.TIMEOUT_FOR_STATUS_FINISHED)

    return None


def destroy_marathon_app(obj, run_async=True):
    try:
        marathon.get_app(obj.marathon_app_id)
    except Exception as e:
        LOG.error(e)
    else:
        marathon.delete_app(obj.marathon_app_id)
        if not run_async:
            while True:
                try:
                    marathon.get_app(obj.marathon_app_id)
                except MarathonHttpError as e:
                    if str(e).find("404") != -1:
                        return
                time.sleep(1)
                continue

    return None


def suspend_marathon_app(obj, run_async=True):
    try:
        marathon.get_app(obj.marathon_app_id)
    except Exception as e:
        LOG.error(e)
    else:
        app = marathon.scale_app(obj.marathon_app_id, instances=0)
        if hasattr(obj, "m_version") and hasattr(obj, "deployment_id"):
            obj.m_version = app['version']
            obj.deployment_id = app['deploymentId']
            obj.save()
        if not run_async:
            app = marathon.get_app(obj.marathon_app_id)
            while app.instances != 0:
                time.sleep(1)
                app = marathon.get_app(obj.marathon_app_id)
                continue
        if hasattr(obj, "check_suspend"):
            obj.check_suspend()

    return None


def get_marathon_client():

    def disable_requests_ssl_verify():
        import requests
        origin_request = requests.request

        def request(*args, **kwargs):
            kwargs['verify'] = False
            return origin_request(*args, **kwargs)
        requests.request = request

    disable_requests_ssl_verify()

    return MarathonClient(settings.MARATHON_SERVERS,
                          username=settings.MARATHON_USERNAME,
                          password=settings.MARATHON_PASSWORD)


marathon = SimpleLazyObject(lambda: get_marathon_client())


def get_image_fullname(image):
    DEFAULT_REGISTRY = "index.xxxxx.com"
    return "{0}/{1}".format(DEFAULT_REGISTRY, image)


def clean_container_path(path):
    return path.replace("/", "-")[1:]
