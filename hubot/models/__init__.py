# -*- coding: utf-8 -*-
import string
import re
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
from model_utils.models import TimeStampedModel


MIN_CPUS = settings.MIN_CPUS
MAX_CPUS = settings.MAX_CPUS
MIN_MEM = settings.MIN_MEM
MAX_MEM = settings.MAX_MEM
MIN_SIZE = settings.MIN_SIZE
MAX_SIZE = settings.MAX_SIZE
MIN_BACKUP_KEEP = settings.MIN_BACKUP_KEEP
MAX_BACKUP_KEEP = settings.MAX_BACKUP_KEEP


def validate_size(value):
    try:
        value = int(value)
    except:
        raise ValidationError("Value '%s' is not an volume size number, must be integer." % value)
    if value > MAX_SIZE or value <= MIN_SIZE:
        raise ValidationError("The interval value of volume size is '{min}-{max}', '{value}' found".format(**{
                              "min": MIN_SIZE, "max": MAX_SIZE, "value": value}))


def validate_cpus(value):
    try:
        value = float(value)
    except:
        raise ValidationError("Value '%s' is not an cpu number, must be float." % value)
    if value > MAX_CPUS or value <= MIN_CPUS:
        raise ValidationError("The interval value of cpu is '{min}-{max}', '{value}' found".format(**{
                              "min": MIN_CPUS, "max": MAX_CPUS, "value": value}))


def validate_mem(value):
    try:
        value = float(value)
    except:
        raise ValidationError("Value '%s' is not an mem number, must be float." % value)
    if value > MAX_MEM or value <= MIN_MEM:
        raise ValidationError("The interval value of mem is '{min}-{max}', '{value}' found".format(**{
                              "min": MIN_MEM, "max": MAX_MEM, "value": value}))


def validate_name(value):
    if not value:
        raise ValidationError("Name can not be none")
    if not re.match(r"[a-z]", value):
        raise ValidationError("The first one of the name must be a letter, '%s' found" % value)
    regex = re.search(r'^(?:[a-z0-9\-]*)', value)
    if not regex:
        raise ValidationError("Please enter a valid 'name' consisting of letters, numbers, and hyphens.")
    if not regex.group() is value:
        raise ValidationError("Name only can be used with numbers, letters and hyphens, '%s' found" % value)


def validate_hour(value):
    try:
        value = int(value)
    except:
        raise ValidationError("Value '%s' is not an hour number, must be integer." % value)
    if not 0 <= value <= 23:
        raise ValidationError("The interval value of hour is '0-23', '{value}' found".format(**{"value": value}))


def validate_minute(value):
    try:
        value = int(value)
    except:
        raise ValidationError("Value '%s' is not an minute number, must be integer." % value)
    if not 0 <= value <= 59:
        raise ValidationError("The interval value of minute is '0-59', '{value}' found".format(**{"value": value}))


def validate_backup_keep(value):
    try:
        value = int(value)
    except:
        raise ValidationError("Value '%s' is not an retention number, must be integer." % value)
    if not MIN_BACKUP_KEEP <= value < MAX_BACKUP_KEEP:
        raise ValidationError("The interval value of retention number is '{min}-{max}', '{value}' found".format(**{
                              "min": MIN_BACKUP_KEEP, "max": MAX_BACKUP_KEEP, "value": value}))


class MesosResourceModel(models.Model):

    cpus = models.FloatField(validators=[validate_cpus])
    mem = models.FloatField(validators=[validate_mem])
    instances = models.IntegerField(default=1)

    class Meta:
        abstract = True


class NamespaceModel(TimeStampedModel):

    name = models.CharField(max_length=128, validators=[validate_name])
    namespace = models.CharField(max_length=32)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ('-modified', '-created')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.get_random_name()
        if self.user:
            self.namespace = self.user.username
        self.clean_fields()
        super(NamespaceModel, self).save(*args, **kwargs)

    def full_name(self, sep='-', namespace_first=True):
        if namespace_first:
            return u"{0}{1}{2}".format(self.namespace, sep, self.name)
        else:
            return u"{0}{1}{2}".format(self.name, sep, self.namespace)

    def get_random_name(self):
        return "{0}-{1}".format(get_random_string(4, allowed_chars=string.lowercase),
                                get_random_string(4, allowed_chars=string.lowercase))
