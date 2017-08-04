# -*- coding: utf-8 -*-
from rest_framework import serializers
from addons.models import AddonMySQL


class AddonsMySQLSerializer(serializers.ModelSerializer):

    class Meta:
        model = AddonMySQL
