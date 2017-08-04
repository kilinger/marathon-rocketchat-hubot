# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm
from accounts.models import CustomUser
from django.utils.translation import ugettext_lazy as _


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'email', 'subnet', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'description', 'tzinfo', 'git_id_rsa')}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2')}),
    )
    list_display = ('username', 'email', 'subnet', 'is_superuser', 'created', 'auth_token')
    list_filter = ('is_superuser', 'email', 'username')
    search_fields = ('username', 'email', 'screen_name', 'tzinfo', 'subnet')
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm


admin.site.register(CustomUser, CustomUserAdmin)
