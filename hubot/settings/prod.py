# -*- coding: utf-8 -*-
# flake8: noqa
from .base import *  # noqa
from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging

DEBUG = False
TEMPLATE_DEBUG = DEBUG


ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


CACHES = {
    'default': env.cache_url(),
    'redis': env.cache_url('REDIS_URL'),
}


COMPRESS_OFFLINE = True


DATABASES = {
    'default': env.db_url()
}


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# Examples: "http://media.lawrence.com/media/",
# "http://example.com/media/""
MEDIA_URL = env('MEDIA_URL')


# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = env('STATIC_URL')


SENTRY_DSN = env('SENTRY_DSN')

INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

handler = SentryHandler(SENTRY_DSN)
setup_logging(handler)

MARATHON_SERVERS = env.list('MARATHON_SERVERS')
MARATHON_USERNAME = env('MARATHON_USERNAME')
MARATHON_PASSWORD = env('MARATHON_PASSWORD')

OS_USER_NAME = env('OS_USERNAME')
OS_PASSWORD = env('OS_PASSWORD')
OS_TENANT_NAME = env('OS_TENANT_NAME')
OS_AUTH_URL = env('OS_AUTH_URL')


MIN_INSTANCES = env.int('MIN_INSTANCES')
MIN_CPUS = env.float('MIN_CPUS')
MAX_CPUS = env.float('MAX_CPUS')
MIN_MEM = env.float('MIN_MEM')
MAX_MEM = env.float('MAX_MEM')
MIN_SIZE = env.int('MIN_SIZE')
MAX_SIZE = env.int('MAX_SIZE')
MIN_BACKUP_KEEP = env.int('MIN_BACKUP_KEEP')
MAX_BACKUP_KEEP = env.int('MAX_BACKUP_KEEP')


TIMEOUT_FOR_STATUS_FINISHED = env.int('TIMEOUT_FOR_STATUS_FINISHED')  # seconds
MINIMUM_HEALTH_CAPACITY = env.float('MINIMUM_HEALTH_CAPACITY')


BUILD_CALLBACK_URI = env('BUILD_CALLBACK_URI')
BUILD_VOLUMES = env('BUILD_VOLUMES')
BUILD_ENVS = env('BUILD_ENVS')
EREMETIC_URL = env('EREMETIC_URL')
EREMETIC_USERNAME = env('EREMETIC_USERNAME')
EREMETIC_PASSWORD = env('EREMETIC_PASSWORD')


BROKER_URL = env('BROKER_URL')

# celery once
ONCE_REDIS_URL = env('ONCE_REDIS_URL')
ONCE_DEFAULT_TIMEOUT = env.int('ONCE_DEFAULT_TIMEOUT')
