# -*- coding: utf-8 -*-
import re
import logging
from django.conf import settings
from django.db.utils import IntegrityError
from docopt import docopt, DocoptExit
from rest_framework.decorators import api_view
from rest_framework.response import Response
from tabulate import tabulate
from schema import Schema, And, Or, Use, SchemaError
from addons.models import Addon, AddonSnapshot
from addons.tasks import create_volume_and_release, restore_addon_snapshot, do_reset
from addons.utils import addons_create, AddonNotFound, get_support_addons
from api.utils import string_to_bool
from hubot.utils.mesos import destroy_marathon_app, create_or_update_marathon_app, get_image_fullname
from projects.models import ProjectConfig, Project, ProjectRelease, ProjectAddon, ProjectBuild
from projects.serializers import ProjectConfigSerializer
from projects.tasks import release_deploy


logger = logging.getLogger('hubot')


MIN_INSTANCES = settings.MIN_INSTANCES
MIN_CPUS = settings.MIN_CPUS
MAX_CPUS = settings.MAX_CPUS
MIN_MEM = settings.MIN_MEM
MAX_MEM = settings.MAX_MEM
MIN_SIZE = settings.MIN_SIZE
MAX_SIZE = settings.MAX_SIZE
MIN_BACKUP_KEEP = settings.MIN_BACKUP_KEEP
MAX_BACKUP_KEEP = settings.MAX_BACKUP_KEEP


class Cmd(object):

    OK = 0
    ERROR = 1

    actions = []

    def __init__(self, user):
        self.user = user
        self.args = None

    def usage(self):
        return self.__doc__

    def get_actions(self):
        return self.actions

    def parse_arguments(self, argv):
        return docopt(self.usage(), argv)

    def error(self, msg=None):
        return self.ERROR, self.usage(), msg or u""

    def success(self, msg=None):
        return self.OK, msg or u"Success", u""

    def run(self, argv):
        # hack for bug fix
        if isinstance(argv, unicode):
            argv = argv.encode("utf-8")
        elif isinstance(argv, list):
            argv = list(v.encode("utf-8") for v in argv)

        try:
            args = self.parse_arguments(argv)
        except DocoptExit:
            return self.error()

        # hack for bug fix
        for key, value in args.items():
            if isinstance(value, str):
                args[key] = value.decode("utf-8")
            elif isinstance(value, list):
                args[key] = list(v.decode("utf-8") for v in value)

        self.args = args

        try:
            return self._run(args)
        except Exception as e:
            return self.error(str(e))

    def _run(self, args):
        action = None
        for key in self.get_actions():
            if args.get(key, False):
                action = getattr(self, key, None)

        if not action:
            return self.error()

        return action(args)

    def get_project(self):
        """
        :rtype: `projects.models.Project`
        """
        project_name = self.args.get('--project') or self.args.get('<project>')
        try:
            project = Project.objects.get(user=self.user, name=project_name)
        except Project.DoesNotExist:
            raise Exception(u"Project '{0}' not found".format(project_name))

        return project

    def get_addon(self):
        name = self.args.get('--addon') or self.args.get('<name>')
        try:
            addon = Addon.objects.get(user=self.user, name=name)
        except Addon.DoesNotExist:
            raise Exception(u"Addon '{0}' not found".format(name))
        return addon


class SnapshotsCmd(Cmd):

    """xxxxx snapshots

    Usage:
      snapshots create -a <addon> [<description>...]
      snapshots destroy <snapshot> -a <addon>
      snapshots restore <snapshot> -a <addon>
      snapshots list -a <addon>

    Options:
      -h, --help                          Show this screen.
      -a <addon>, --addon=<addon>         Addon's name
    """

    actions = ['create', 'destroy', 'restore', 'list']

    def get_schema(self):
        schema = Schema({
            '--addon': Or(None, lambda n: re.search(r"[a-zA-Z][a-zA-Z0-9\-]*", n).group() == n,
                          error='"--addon" only can be used with numbers, letters, hyphens and initial with letter'),
            '<snapshot>': Or(None, lambda n: re.search(r"^[1-9][0-9]*$", n),
                             error='"<snapshot>" must be used with numbers, eg: 1, 2, 3...'),
        })
        return schema

    def get_real_addon(self, args):
        schema = self.get_schema()
        try:
            schema.validate({"--addon": args["--addon"], "<snapshot>": args["<snapshot>"]})
        except SchemaError as e:
            return self.error(str(e))
        addon = self.get_addon().real_addon
        if not addon.has_snapshot_support():
            return self.error("Addon type of '{0}' don't have operate for snapshots".format(addon.addon_name))
        return addon

    def create(self, args):
        addon = self.get_real_addon(args)
        if isinstance(addon, tuple):
            return addon
        if len(args["<description>"]) > 1:
            description = " ".join(args["<description>"])
        elif len(args["<description>"]) == 1:
            description = args["<description>"][0]
        else:
            description = ""
        try:
            addon.create_snapshot(description)
        except Exception as e:
            return self.error(str(e))
        return self.success()

    def destroy(self, args):
        addon = self.get_real_addon(args)
        if isinstance(addon, tuple):
            return addon
        snapshot_id = args["<snapshot>"]
        try:
            addon.destroy_snapshot(snapshot_id)
        except Exception as e:
            return self.error(str(e))
        return self.success()

    def restore(self, args):
        addon = self.get_real_addon(args)
        if isinstance(addon, tuple):
            return addon
        snapshot_id = args["<snapshot>"]
        try:
            snapshot = AddonSnapshot.objects.get(addon=addon, short_id=snapshot_id)
        except AddonSnapshot.DoesNotExist as e:
            return self.error(str(e))
        try:
            restore_addon_snapshot.apply_async(args=[addon, snapshot])
        except Exception as e:
            return self.error(str(e))
        return self.success()

    def list(self, args):
        addon = self.get_addon()
        snapshots = addon.snapshots.all()

        headers = ["Snapshot", "Create", "Description"]
        table = []
        for snapshot in snapshots:
            table.append([snapshot.short_id, self.user.get_time_display(snapshot.created), snapshot.description])

        out = tabulate(table, headers=headers, tablefmt="simple")

        return self.success(out)


class AddonsCmd(Cmd):

    """xxxxx addons

    Usage:
      addons create <service> --project=<project> [options]
      addons scale <name> [options]
      addons destroy <name>
      addons info <name>
      addons reset <name>
      addons attach <name> --project=<project> [options]
      addons detach <name> --project=<project>
      addons list [--project=<project>]
      addons services

    Options:
      -h, --help                                        Show this screen.
      -a <alias>, --as=<alias>                          Addon's alias name attached to project
      -n <name>, --name=<name>                          Addon's name (ignore in attach)
      -c <cpus>, --cpus=<cpus>                          Addon's cpus num, default=1 (ignore in attach)
      -m <mem>, --mem=<mem>                             Addon's mem(MB), default=512 (ignore in attach)
      -p <project>, --project=<project>                 Project name
      -s <size>, --size=<size>                          Addon's volume size(GB), default=16
      --state=<state>                                   Addon's state, choices are 'down' or 'up', [default: up]
      --backup-hour=<backup-hour>                       Hour in the day to auto create snapshot task, default=0
      --backup-minute=<backup-minute>                   Minute in the day to auto create snapshot task, default=0
      --backup-keep=<backup-keep>                       Addon's Snapshots number to keep, default=7
      --backup-enable                                   Execute task to enable create snapshot everyday
    """

    actions = ['attach', 'create', 'detach', 'destroy', 'info', 'list', 'services', 'scale', 'reset']

    def get_schema(self):
        schema = Schema({
            '--mem': Or(None, And(Use(float), lambda n: MIN_MEM < n <= MAX_MEM),
                        error='--mem=<mem> should be float {0} < mem <= {1}'.format(MIN_MEM, MAX_MEM)),
            '--cpus': Or(None, And(Use(float), lambda n: MIN_CPUS < n <= MAX_CPUS),
                         error='--cpus=<cpus> should be float {0} < cpus <= {1}'.format(MIN_CPUS, MAX_CPUS)),
            '--name': Or(None, lambda n: re.search(r"[a-zA-Z][a-zA-Z0-9\-]*", n).group() == n,
                         error='Name only can be used with numbers, letters, hyphens and initial with letter'),
            '--size': Or(None, And(Use(int), lambda n: MIN_SIZE < n <= MAX_SIZE),
                         error='--size=<size> should be integer {0} < size <= {1}'.format(MIN_SIZE, MAX_SIZE)),
            '--backup-hour': Or(None, And(Use(int), lambda n: 0 <= n <= 23),
                                error='--backup-hour=<backup-hour> should be integer 0 <= backup-hour <= 23'),
            '--backup-minute': Or(None, And(Use(int), lambda n: 0 <= n <= 59),
                                  error='--backup-minute=<backup-minute> should be integer 0 <= backup-minute <= 59'),
            '--state': Or(None, And(Use(lambda n: n in ["up", "down"])),
                          error='Option --state should be used "up" or "down".'),
            '--backup-keep': Or(None, And(Use(int), lambda n: MIN_BACKUP_KEEP < n <= MAX_BACKUP_KEEP),
                                error='Option --backup-keep should be integer {0} < backup-keep <= {1}'.format(
                                    MIN_BACKUP_KEEP, MAX_BACKUP_KEEP)),

        })
        return schema

    def scale(self, args):
        schema = self.get_schema()
        try:
            schema.validate({"--cpus": args["--cpus"], "--mem": args["--mem"], "--name": args["--name"],
                             "--size": args['--size'], "--backup-hour": args["--backup-hour"],
                             "--backup-minute": args["--backup-minute"], "--backup-keep": args["--backup-keep"],
                             "--state": args["--state"]})
        except SchemaError as e:
            return self.error(str(e))

        addon = self.get_addon()

        changed = False
        for key in ['cpus', 'mem']:
            if args['--' + key]:
                setattr(addon, key, args['--' + key])
                changed = True
        if changed:
            addon.save()

        if addon.depend:
            create_or_update_marathon_app(addon.depend.real_addon)
        create_or_update_marathon_app(addon.real_addon)
        return self.success(u"Addon {0} scale to cpus {1} mem {2}".format(addon.name, addon.cpus, addon.mem))

    def attach(self, args):
        addon = self.get_addon()
        project = self.get_project()
        try:
            addon.attach(project, alias=args['--as'] if args['--as'] else '')
        except IntegrityError:
            return self.error(u"Addon '{0}' is already attach to Project '{1}'".format(addon.name, project.name))
        except Exception as e:
            return self.error(unicode(e))
        return self.success()

    def detach(self, args):
        addon = self.get_addon()
        project = self.get_project()
        addon.detach(project)
        return self.success()

    def create(self, args):
        schema = self.get_schema()
        try:
            schema.validate({"--cpus": args["--cpus"], "--mem": args["--mem"], "--name": args["--name"],
                             "--size": args["--size"], "--backup-hour": args["--backup-hour"],
                             "--backup-minute": args["--backup-minute"], "--backup-keep": args["--backup-keep"],
                             "--state": args["--state"]})
        except SchemaError as e:
            return self.error(str(e))

        project = self.get_project()

        service = args['<service>']
        if Addon.objects.filter(name=args['--name'], user=self.user).exists():
            return self.error(u"Addon name '{0}' already exists".format(args['--name']))
        try:
            addon = addons_create(self.user, service, args['--name'], args['--cpus'], args['--mem'],
                                  size=args['--size'], backup_hour=args['--backup-hour'],
                                  backup_minute=args['--backup-minute'], backup_keep=args['--backup-keep'],
                                  backup_enable=args['--backup-enable'])
        except AddonNotFound:
            return self.error(u"Service '{0}' not found".format(service))

        if args['--state'] == 'up':
            if addon.depend:
                create_volume_and_release.apply_async(args=[addon.depend.real_addon, True])
            create_volume_and_release.apply_async(args=[addon, True])
        try:
            addon.attach(project, alias=args['--as'] if args['--as'] else '')
        except IntegrityError:
            return self.error(u"Addon '{0}' is already attach to Project '{1}'".format(addon.name, project.name))
        except Exception as e:
            return self.error(unicode(e))

        return self.success(u"Addon {0} created".format(addon.name))

    def reset(self, args):
        addon = self.get_addon().real_addon
        try:
            do_reset.apply_async(args=[addon])
        except Exception as e:
            return self.error(str(e))
        return self.success(u"Addon {0} reset success".format(addon.name))

    def destroy(self, args):
        addon = self.get_addon()

        addon.detach()
        addon.delete()
        destroy_marathon_app(addon)

        return self.success(u"Addon {0} destroyed".format(addon.name))

    def info(self, args):
        addon = self.get_addon().real_addon
        config = addon.get_config()
        table = [["Addon info"]]

        table.append(["Name", addon.name])
        table.append(["Cpus", addon.cpus])
        table.append(["Mem", addon.mem])
        table.append(["Service", addon.addon_name])
        table.append(["Config", unicode(config)[1:-1]])
        table.append(["Host", addon.get_host()])

        out = tabulate(table, headers="firstrow", tablefmt="simple")

        return self.success(out)

    def list(self, args):
        addons = Addon.objects.filter(user=self.user)

        headers = ["Name", "Status", "Service", "Project"]

        project = self.get_project() if args["--project"] else None
        table = []
        for addon in addons:
            pa = ProjectAddon.objects.filter(addon=addon)
            name = ",".join(pa.values_list("project__name",
                                           flat=True)) if pa.count() > 1 else pa[0].project.name if pa else ""
            if project and name.find(project.name) < 0:
                continue
            table.append([addon.name, addon.status, addon.slug, name])

        table.sort()
        out = tabulate(table, headers=headers, tablefmt="simple")

        return self.success(out)

    def services(self, args):
        table = [["Slug", "Default Version"]]
        for name, cls in get_support_addons().items():
            table.append([name, cls.get_default_version()])
        table.sort()
        out = tabulate(table, headers="firstrow", tablefmt="simple")

        return self.success(out)


class ProjectsCmd(Cmd):

    """xxxxx projects

    Usage:
      projects create [<name>] [options]
      projects destroy <project>
      projects info <project>
      projects scale <project> [options]
      projects list

    Options:
      -h, --help                                        Show this screen.
      -d <domain>, --domain=<domain>                    Custom domain for project
      -c <cpu>, --cpus=<cpus>                           Cpus for project
      -m <mem>, --mem=<mem>                             Memory for project
      -i <instances>, --instances=<instances>           Instances running of this project
      --health-check=<health_check>                     Health check path for project, default is /
      --no-health-check                                 Disable health check
      --git-repo=<git-repo>                             Project git repository to clone and build
      --git-id-rsa=<git-id-rsa>                         Private SSH key to use when cloning the git repository
      --redirect-https=<redirect-https>                 Redirect HTTP traffic to HTTPS, write 'true' to enable
      --use-hsts=<use-hsts>                             HSTS response header for HTTP clients, write 'true' to enable
      --use-lb=<use-lb>                                 Project's marathon-lb, write 'false' to disable

    Overview of health_check:
      a request for the '/'(slash) URI is made to each server in the upstream group every 5 seconds (the default).
      Servers that respond with a well-formed 2xx or 3xx response are considered healthy; otherwise they are marked
      as failed. '--health-check' will be expire when '--no-health-check' used.
    """

    actions = ['create', 'destroy', 'info', 'scale', 'list']

    def get_schema(self):
        schema = Schema({
            '--instances': Or(None, And(Use(int), lambda n: MIN_INSTANCES < n),
                        error='--instances=<instances> should be int {0} < instances'.format(MIN_INSTANCES)),
            '--mem': Or(None, And(Use(float), lambda n: MIN_MEM < n <= MAX_MEM),
                        error='--mem=<mem> should be float {0} < mem <= {1}'.format(MIN_MEM, MAX_MEM)),
            '--cpus': Or(None, And(Use(float), lambda n: MIN_CPUS < n <= MAX_CPUS),
                         error='--cpus=<cpus> should be float {0} < cpus <= {1}'.format(MIN_CPUS, MAX_CPUS)),
            '<name>': Or(None, lambda n: re.search(r"[a-zA-Z][a-zA-Z0-9\-]*", n).group() == n,
                         error='Name only can be used with numbers, letters, hyphens and initial with letter'),
        })
        return schema

    def get_health_check(self):
        health_check = "/"
        if self.args['--health-check']:
            health_check = self.args['--health-check']
        if self.args['--no-health-check']:
            health_check = ""
        return health_check

    def create(self, args):
        schema = self.get_schema()
        try:
            schema.validate({"--cpus": args["--cpus"], "--mem": args["--mem"], "<name>": args["<name>"],
                             "--instances": args["--instances"]})
        except SchemaError as e:
            return self.error(str(e))

        health_check = self.get_health_check()
        use_lb = string_to_bool(args["--use-lb"]) if args["--use-lb"] else True
        try:
            project = Project.objects.create(user=self.user, name=args['<name>'], health_check=health_check,
                                             cpus=args['--cpus'] or 1, mem=args['--mem'] or 512,
                                             instances=args['--instances'] or 1, domain=args['--domain'] or '',
                                             git_id_rsa=args['--git-id-rsa'] or '', git_repo=args['--git-repo'] or '',
                                             use_lb=use_lb)
        except IntegrityError:
            return self.error(u"Project name '{0}' already exists".format(args['<name>']))
        except Exception as e:
            return self.error(unicode(e))

        out = u"Project {0} created".format(project.name)
        return self.success(out)

    def destroy(self, args):
        project = self.get_project()

        releases = ProjectRelease.objects.filter(project=project).order_by("-modified")
        if releases.exists():
            destroy_marathon_app(releases[0])

        project.delete()
        return self.success(u"Project '{0}' destroyed".format(project.name))

    def info(self, args):
        project = self.get_project()

        table = [["Project info"]]

        table.append(["Name", project.name])
        table.append(["Cpus", project.cpus])
        table.append(["Mem", project.mem])
        table.append(["Instances", project.instances])
        table.append(["Host", project.get_host()])
        if project.domain:
            table.append(["Domain", project.domain])
        table.append(["Health check", project.health_check])

        out = tabulate(table, headers="firstrow", tablefmt="simple")

        return self.success(out)

    def scale(self, args):
        schema = self.get_schema()
        try:
            schema.validate({"--cpus": args["--cpus"], "--mem": args["--mem"], "<name>": args["<name>"],
                             "--instances": args["--instances"]})
        except SchemaError as e:
            return self.error(str(e))

        project = self.get_project()

        if args["--cpus"]:
            project.cpus = args["--cpus"]
        if args["--mem"]:
            project.mem = args["--mem"]
        if args["--instances"]:
            project.instances = args["--instances"]
        if args['--health-check']:
            project.health_check = args['--health-check']
        if args['--no-health-check']:
            project.health_check = ""
        if args['--domain']:
            project.domain = args['--domain']
        if args['--git-repo']:
            project.git_repo = args['--git-repo']
        if args['--git-id-rsa']:
            project.git_repo = args['--git-id-rsa']
        if args['--redirect-https']:
            project.redirect_https = string_to_bool(args['--redirect-https'])
        if args['--use-hsts']:
            project.use_hsts = string_to_bool(args['--use-hsts'])
        if args['--use-lb']:
            project.use_lb = string_to_bool(args["--use-lb"])
        try:
            project.save()
        except Exception as e:
            return self.error(str(e))
        try:
            release = ProjectRelease.objects.filter(project=project,
                                                    status=ProjectRelease.STATUS.Running).order_by("-modified")[0]
        except Exception as e:
            logger.error(str(e))
        else:
            release_deploy(release.id, enqueue=True)

        return self.success()

    def list(self, args):
        projects = Project.objects.filter(user=self.user)

        headers = ["Name"]
        table = []
        for project in projects:
            table.append([project.name])

        table.sort()
        out = tabulate(table, headers=headers, tablefmt="simple")

        return self.success(out)


class ConfigCmd(Cmd):

    """xxxxx config

    Usage:
      config set --project=<project> <key=value>...
      config get --project=<project> <key>
      config unset --project=<project> <key>...
      config list --project=<project>

    Options:
      -h, --help                          Show this screen.
      -p <project>, --project=<project>   Project name
    """

    actions = ['set', 'get', 'unset', 'list']

    def set(self, args):
        project = self.get_project()

        kvs = args["<key=value>"]
        for kv in kvs:
            try:
                key, value = kv.split("=", 1)
            except:
                return self.error(u"Key '{0}' must be format 'key=value'".format(kv))

            try:
                config = ProjectConfig.objects.get(key=key.upper(), project_id=project.id)
            except ProjectConfig.DoesNotExist:
                config = None

            data = dict(project=project.id, key=key, value=value)
            serializer = ProjectConfigSerializer(config, data=data, partial=True if config else False)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return self.success()

    def get(self, args):
        project = self.get_project()
        configs = project.get_configs()

        key = args["<key>"][0]
        value = configs.get(key.upper()) or u"No value for '{0}'".format(key.upper())
        return self.success(value)

    def unset(self, args):
        project = self.get_project()

        keys = args["<key>"]
        for key in keys:
            key = key.upper()
            try:
                config = ProjectConfig.objects.get(project_id=project.id, key=key)
            except ProjectConfig.DoesNotExist:
                return self.error(u"Config key '{0}' not found".format(key))

            config.delete()
        return self.success()

    def list(self, args):
        project = self.get_project()

        configs = project.get_configs()

        headers = ["Key", "Value"]
        table = []
        for key, value in configs.items():
            table.append([key, value])

        table.sort()
        out = tabulate(table, headers=headers, tablefmt="simple")

        return self.success(out)


class ReleasesCmd(Cmd):

    """xxxxx releases

    Usage:
      releases create <tag> --project=<project> [options]
      releases list --project=<project>

    Options:
      -h, --help                          Show this screen.
      -p <project>, --project=<project>   Project name
      -f, --force                         Force releases
      --no-build                          Don't build code
    """

    actions = ['create', 'list']

    def create(self, args):
        project = self.get_project()
        release = project.create_release(args["<tag>"])

        if release.build.status == ProjectBuild.STATUS.Finished or args['--no-build']:
            release_deploy(release.id, force=args["--force"], enqueue=True)
            return self.success("Release {0} of project {1} created".format(release.build.tag, project.name))

        if not project.git_repo or not (project.git_id_rsa or self.user.git_id_rsa):
            return self.error("Please use 'xxxxx projects {0} scale --git-repo XXX' to set them".format(
                              args['--project']))

        image_name = get_image_fullname(release.get_container_image())
        release.build.do_build(image_name)
        return self.success("Release {0} of project {1} created, please waiting for build".format(
                            release.build.tag, project.name))

    def list(self, args):
        project = self.get_project()
        releases = ProjectRelease.objects.filter(project=project).order_by("-created")[:50]

        headers = ["Tag", "Create", "Status"]
        table = []

        for release in releases:
            table.append([release.build.tag, self.user.get_time_display(release.created), release.status])

        out = tabulate(table, headers=headers, tablefmt="simple")

        return self.success(out)


class xxxxxCmd(Cmd):
    """xxxxx

    Usage: xxxxx <command> [<args>...]

    Options:
      -h, --help                          Show this screen.

    The most commonly used xxxxx commands are:
      projects     List, create or destroy projects
      addons       List, create or destroy addons
      snapshots    List, create or destroy snapshots
      config       List, set or unset project config
      releases     List, release project releases
    """

    program = "xxxxx"

    def parse_arguments(self, argv):
        if argv.startswith(self.program):
            argv = argv.replace(self.program, "", 1).strip()

        return docopt(self.usage(), argv, options_first=True)

    def _run(self, args):
        argv = args['<args>']
        command = args['<command>']

        if command in ['help', '-h']:
            if argv:
                command = argv[0]
                argv = argv[1:] + ["help"]

        if command == 'projects':
            return self.projects.run(argv)
        elif command == 'addons':
            return AddonsCmd(self.user).run(argv)
        elif command == 'config':
            return ConfigCmd(self.user).run(argv)
        elif command == 'releases':
            return ReleasesCmd(self.user).run(argv)
        elif command == 'snapshots':
            return SnapshotsCmd(self.user).run(argv)
        elif command in ['help', '-h']:
            return self.success(self.usage())
        else:
            return self.error()

    def help(self, argv):
        return self.success()

    @property
    def projects(self):
        return ProjectsCmd(self.user)


@api_view(['POST', 'OPTIONS'])
def run(request):
    cmd = request.data.get("cmd", "").strip()
    print 'run cmd:', cmd.encode("utf-8")
    rc, out, err = xxxxxCmd(request.user).run(cmd)
    return Response(data=dict(rc=rc, cmd=cmd, stdout=out, stderr=err))
