# -*- coding: utf-8 -*-
# flake8: noqa
from .base import *  # noqa


SITE_TITLE = SITE_TITLE + gettext_noop(u'(开发版)')


CACHES = {
    'default': env.cache_url(default='memcache://127.0.0.1:11211'),
    'redis': env.cache_url('REDIS_URL', default='redis://127.0.0.1:6379/0'),
}


DATABASES = {
    'default': env.db_url(default='postgresql://postgres:@127.0.0.1:5432/hubot')
}


MEDIA_URL = env('MEDIA_URL', default='/media/')


STATIC_URL = env('STATIC_URL', default='/static/')


try:
    import debug_toolbar  # noqa
except ImportError:
    HAS_DEBUG_TOOLBAR = False
else:
    HAS_DEBUG_TOOLBAR = True

if HAS_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar', 'template_timings_panel')
    DEBUG_TOOLBAR_PATCH_SETTINGS = False
    INTERNAL_IPS = [env('INTERNAL_IPS', default='127.0.0.1')]
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware', )

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',

        'template_timings_panel.panels.TemplateTimings.TemplateTimings',
    ]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


try:
    import django_extensions  # noqa
except ImportError:
    django_extensions = None
else:
    INSTALLED_APPS += ('django_extensions', )


try:
    import dbbackup  # noqa
except ImportError:
    dbbackup = None
else:
    INSTALLED_APPS += ('dbbackup', )
    DBBACKUP_STORAGE = 'dbbackup.storage.filesystem_storage'
    DBBACKUP_FILESYSTEM_DIRECTORY = root('../backups', ensure=True)


MARATHON_SERVERS = env.list('MARATHON_SERVERS', default=['http://127.0.0.1:8080'])
MARATHON_USERNAME = env('MARATHON_USERNAME', default=None)
MARATHON_PASSWORD = env('MARATHON_PASSWORD', default=None)


OS_USER_NAME = env('OS_USERNAME', default=None)
OS_PASSWORD = env('OS_PASSWORD', default=None)
OS_TENANT_NAME = env('OS_TENANT_NAME', default=None)
OS_AUTH_URL = env('OS_AUTH_URL', default=None)


MIN_INSTANCES = env.int('MIN_INSTANCES', default=0)
MIN_CPUS = env.float('MIN_CPUS', default=0)
MAX_CPUS = env.float('MAX_CPUS', default=8)
MIN_MEM = env.float('MIN_MEM', default=0)
MAX_MEM = env.float('MAX_MEM', default=16 * 1024)
MIN_SIZE = env.int('MIN_SIZE', default=0)
MAX_SIZE = env.int('MAX_SIZE', default=1000)
MIN_BACKUP_KEEP = env.int('MIN_BACKUP_KEEP', default=0)
MAX_BACKUP_KEEP = env.int('MAX_BACKUP_KEEP', default=100)


TIMEOUT_FOR_STATUS_FINISHED = env.int('TIMEOUT_FOR_STATUS_FINISHED', default=60 * 15)  # seconds
MINIMUM_HEALTH_CAPACITY = env.float('MINIMUM_HEALTH_CAPACITY', default=0.6)


BUILD_CALLBACK_URI = env('BUILD_CALLBACK_URI', default="http://127.0.0.1:8000")
BUILD_VOLUMES = env('BUILD_VOLUMES', default="/var/run/docker.sock:/var/run/docker.sock, /root/.docker:/.docker")
BUILD_ENVS = env('BUILD_ENVS', default="DOCKER_DAEMON_ARGS=--mtu=1450")
EREMETIC_URL = env('EREMETIC_URL', default="http://127.0.0.1:8000")
EREMETIC_USERNAME = env('EREMETIC_USERNAME', default=None)
EREMETIC_PASSWORD = env('EREMETIC_PASSWORD', default=None)


BROKER_URL = env('BROKER_URL', default="amqp://username:password@127.0.0.1:5672/")

# celery once
ONCE_REDIS_URL = env('ONCE_REDIS_URL', default='redis://127.0.0.1:6379/0')
ONCE_DEFAULT_TIMEOUT = env.int('ONCE_DEFAULT_TIMEOUT', default=60 * 60)
