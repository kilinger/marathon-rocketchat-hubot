# -*- coding: utf-8 -*-
from django.test import TestCase
from accounts.factories import CustomUserFactory
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser


class CustomUserTest(TestCase):

    def setUp(self):
        self.user = CustomUserFactory()

    def test_create_token(self):
        token = Token.objects.all()[0]
        self.assertEqual(self.user.auth_token, token)
        CustomUserFactory.create_batch(10)
        user_count = CustomUser.objects.all().count()
        token_count = Token.objects.all().count()
        self.assertEqual(user_count, token_count)
        self.assertEqual(user_count, 11)
