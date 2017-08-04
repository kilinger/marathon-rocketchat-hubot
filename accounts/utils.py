# -*- coding: utf-8 -*-
import pytz
from model_utils import Choices
from django.contrib.auth.hashers import make_password


def get_user(username):
    from accounts.models import CustomUser
    try:
        user = CustomUser.objects.get(username=username)
    except:
        password = make_password(username)
        email = username + "@xxxxx.com"
        user = CustomUser.objects.create(username=username, password=password, email=email)
    return user


def get_all_timezones():
    ALL_TIMEZONES = pytz.all_timezones
    choices = Choices()
    for timezone in ALL_TIMEZONES:
        choices += Choices(timezone)
    return choices
