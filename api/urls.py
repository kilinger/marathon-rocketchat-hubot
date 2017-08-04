# -*- coding: utf-8 -*-
from django.conf.urls import include, patterns, url
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from api.views import execute

router = DefaultRouter()


urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'^execute', execute.run),
)
