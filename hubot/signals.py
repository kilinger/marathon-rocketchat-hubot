# -*- coding: utf-8 -*-
from django.dispatch import Signal


status_update_event = Signal(providing_args=["data"])
deployment_success = Signal(providing_args=["data"])
