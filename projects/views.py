# -*- coding: utf-8 -*-
import os
from django.http import HttpResponse


def version(request):
    return HttpResponse(os.environ.get("APP_VERSION", os.environ.get("DJANGO_SETTINGS_MODULE").split(".")[-1]))
