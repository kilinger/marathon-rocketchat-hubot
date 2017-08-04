# -*- coding: utf-8 -*-
import logging
import random

from django.conf import settings
from django_redis import get_redis_connection


logger = logging.getLogger('hubot')


def get_redis_client():
    return get_redis_connection('redis')


client = get_redis_client()


def get_requests_herders(method):
    headers = {
        "Authorization": "Token " + settings.HUBOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    if method == "patch":
        headers["X-HTTP-Method-Override"] = "PATCH"
        return headers
    return headers


def string_to_bool(value):
    try:
        value = str(value)
    except Exception as e:
        logger.error(str(e))
        return False
    else:
        return value.lower() in ["true", "t", "yes", "y"]


def get_random_hour():
    return random.randint(0, 23)


def get_random_minute():
    return random.randint(0, 59)
