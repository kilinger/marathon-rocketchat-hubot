# -*- coding: utf-8 -*-
# flake8: noqa
from .dev import *  # noqa


BROWSER_DRIVER_NAME = env('BROWSER_DRIVER_NAME', default='django')


CACHES = {
    'default': env.cache_url(default='locmemcache://'),
    'redis': env.cache_url(default='redis://127.0.0.1:6379/0')
}


DATABASES = {
    'default': env.db_url(default='sqlite://:memory:'),
}


DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)


# INSTALLED_APPS += ('discover_runner', )
# TEST_RUNNER = 'discover_runner.DiscoverRunner'
# TEST_DISCOVER_TOP_LEVEL = root('../')
