# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from rest_framework.authtoken import views
from django.contrib import admin
from django.conf import settings
from hubot.views import build_notify
from projects.views import version


admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^token/', views.obtain_auth_token),
    url(r'^builds/notify/', build_notify),
    url(r'^version/', version)
)


if settings.DEBUG:
    urlpatterns = patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ) + urlpatterns


if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += patterns(
        '',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
