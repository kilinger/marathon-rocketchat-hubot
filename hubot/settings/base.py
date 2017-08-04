# -*- coding: utf-8 -*-
from hubot.settings import root, env
from celery.schedules import crontab


# Full filesystem path to the project.
PROJECT_ROOT = root('.')

# Name of the project.
PROJECT_NAME = 'hubot'


def gettext_noop(s):
    return s

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-hans'

SITE_ID = 1

SITE_TITLE = gettext_noop(u'HUBOT')

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = root('../media')


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = root('../site-static')


# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    root('static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = env('SECRET_KEY', default='{{ secret_key }}')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'hubot.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'hubot.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    root('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'rest_framework.authtoken',

    'accounts',
    'addons',
    'api',
    'projects',
    'hubot',
)


LOGIN_URL = '/auth/login/'
LOGOUT_URL = '/auth/logout'
DEFAULT_REDIRECT_URL = '/'

# cache-machine 使用的 cache 前缀, 默认为项目的名称
CACHE_PREFIX = 'hubot'

CRISPY_TEMPLATE_PACK = 'bootstrap'


# email configuration
email_config = env.email_url(default='consolemail://')
vars().update(email_config)
EMAIL_SUBJECT = u'change_me'

# APPEND_SLASH = False
AUTH_USER_MODEL = 'accounts.CustomUser'
HUBOT_DOMAIN = env('HUBOT_DOMAIN', default='xxxxx.com')
USE_QUEUE = env.bool('USE_QUEUE', default=False)
HUBOT_API_HOST = env('HUBOT_API_HOST', default="http://127.0.0.1:8000/api")
HUBOT_API_TOKEN = env('HUBOT_API_TOKEN', default="9e4cb9ed7bd006a4f81cbe05f5f2702ae8497729")

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',

    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),

    # Pagination
    'PAGE_SIZE': 20,
    'PAGE_SIZE_QUERY_PARAM': 'count',
    # 'PAGINATE_BY_PARAM': 'count',
    'MAX_PAGE_SIZE': 100,
    # 'MAX_PAGINATE_BY': 100,

    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    # Add other DateTimeField format for djangorestframework-filters. except ISO 8601.
    'DATETIME_INPUT_FORMATS': '%Y-%m-%d %H:%M:%S',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

CELERYBEAT_SCHEDULE = {
    # Executes addons.tasks.create_snapshot_task everyday at 0:00 A.M
    'create_snapshots-everyday-midnight': {
        'task': 'addons.tasks.create_snapshot_task',
        'schedule': crontab(hour=0, minute=0),
        'args': []
    },
}
CELERY_TIMEZONE = 'Asia/Shanghai'
