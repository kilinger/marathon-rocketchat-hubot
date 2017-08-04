# -*- coding:utf-8 -*-
import re
import pytz
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from rest_framework.authtoken.models import Token
from accounts.utils import get_all_timezones
from projects.utils import get_subnet


@python_2_unicode_compatible
class CustomUser(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    email = models.EmailField(_('email address'), max_length=254, unique=True)
    username = models.CharField(_('username'), max_length=30, unique=True,
                                help_text=_('Required. 30 characters or fewer. Letters, '
                                            'numbers and @/./+/-/_ characters'),
                                validators=[
                                    validators.RegexValidator(re.compile('^[\w.@+-]+$'),
                                                              _('Enter a valid username.'), 'invalid')])
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    screen_name = models.CharField(max_length=20, blank=True, null=True, verbose_name=_(u'显示名称'))
    description = models.CharField(max_length=50, blank=True, verbose_name=_(u'描述'))

    subnet = models.CharField(max_length=32, default=get_subnet, verbose_name=_(u"网段"))
    tzinfo = models.CharField(max_length=32, choices=get_all_timezones(), blank=True, null=True, verbose_name=_(u"时区"))
    git_id_rsa = models.TextField(help_text=_(u"The private SSH key to use when cloning the git repository"),
                                  blank=True, verbose_name=_(u"SSH私钥"))

    objects = UserManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return u"%s (%s)" % (self.username, self.email)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        from django.core.mail import send_mail

        send_mail(subject, message, from_email, [self.email])

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url

    @property
    def avatar_url(self):
        return self.get_avatar_url()

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        # Simplest possible answer: All admins are staff
        return self.is_superuser

    def get_time_display(self, time):
        if self.tzinfo:
            time = time.astimezone(pytz.timezone(self.tzinfo))
        return time.strftime("%Y-%m-%d %H:%M:%S %Z%z")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
