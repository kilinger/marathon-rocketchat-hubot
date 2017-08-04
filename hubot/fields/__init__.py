# -*- coding: utf-8 -*-
import string
from django.db import models
from django.utils import six
from django.utils.crypto import get_random_string


MAX_UNIQUE_QUERY_ATTEMPTS = 100


class UpperCaseCharField(models.CharField):

    def __init__(self, *args, **kwargs):
        super(UpperCaseCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            value = value.upper()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(UpperCaseCharField, self).pre_save(model_instance, add)


class RandomCharField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', True)

        self.length = kwargs.pop('length', None)
        if self.length is None:
            raise ValueError("missing 'length' argument")
        kwargs.setdefault('max_length', self.length)

        self.lowercase = kwargs.pop('lowercase', False)
        self.check_is_bool('lowercase')
        self.uppercase = kwargs.pop('uppercase', False)
        self.check_is_bool('uppercase')
        if self.uppercase and self.lowercase:
            raise ValueError("the 'lowercase' and 'uppercase' arguments are mutually exclusive")
        self.include_digits = kwargs.pop('include_digits', True)
        self.check_is_bool('include_digits')
        self.include_alpha = kwargs.pop('include_alpha', True)
        self.check_is_bool('include_alpha')
        self.include_punctuation = kwargs.pop('include_punctuation', False)
        self.check_is_bool('include_punctuation')

        # Set unique=False unless it's been set manually.
        if 'unique' not in kwargs:
            kwargs['unique'] = False

        super(RandomCharField, self).__init__(*args, **kwargs)

    def check_is_bool(self, attrname):
        if not isinstance(getattr(self, attrname), bool):
            raise ValueError("'{}' argument must be True or False".format(attrname))

    def random_char_generator(self, chars):
        for i in range(MAX_UNIQUE_QUERY_ATTEMPTS):
            yield ''.join(get_random_string(self.length, chars))
        raise RuntimeError('max random character attempts exceeded (%s)' %
                           MAX_UNIQUE_QUERY_ATTEMPTS)

    def pre_save(self, model_instance, add):
        if not add and getattr(model_instance, self.attname) != '':
            return getattr(model_instance, self.attname)

        population = ''
        if self.include_alpha:
            if self.lowercase:
                population += string.ascii_lowercase
            elif self.uppercase:
                population += string.ascii_uppercase
            else:
                population += string.ascii_letters

        if self.include_digits:
            population += string.digits

        if self.include_punctuation:
            population += string.punctuation

        random_chars = self.random_char_generator(population)
        new = six.next(random_chars)
        setattr(model_instance, self.attname, new)
        return new

    def deconstruct(self):
        name, path, args, kwargs = super(RandomCharField, self).deconstruct()
        kwargs['length'] = self.length
        if self.lowercase is True:
            kwargs['lowercase'] = self.lowercase
        if self.uppercase is True:
            kwargs['uppercase'] = self.uppercase
        if self.include_alpha is False:
            kwargs['include_alpha'] = self.include_alpha
        if self.include_digits is False:
            kwargs['include_digits'] = self.include_digits
        if self.include_punctuation is True:
            kwargs['include_punctuation'] = self.include_punctuation
        if self.unique is True:
            kwargs['unique'] = self.unique
        return name, path, args, kwargs
