# -*- coding: utf-8 -*-
import factory
from accounts.models import CustomUser
from projects.utils import get_subnet


class CustomUserFactory(factory.DjangoModelFactory):

    username = factory.Sequence(lambda a: "username{0}".format(a))
    email = factory.Sequence(lambda a: "email{0}@example.com".format(a))
    subnet = factory.Sequence(lambda a: get_subnet())
    password = factory.PostGenerationMethodCall('set_password', '111111')

    class Meta:
        model = CustomUser
