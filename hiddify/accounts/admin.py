# accounts/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import CustomUser, Profile
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


# A helper function to display boolean values as icons
def boolean_icon(field_val):
    icon_url = f"/static/admin/img/icon-{'yes' if field_val else 'no'}.svg"
    return format_html('<img src="{}" alt="{}">', icon_url, field_val)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the custom user model.
    Inherits from UserAdmin to get all its features, including the password change form.
    """
    # Fields to display in the main list view of users
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    # Fields to search by in the admin
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # The 'fieldsets' attribute defines the layout of the user edit page.
    # We take the default UserAdmin fieldsets and replace 'username' with 'email'.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # The 'add_fieldsets' attribute defines the layout of the "add user" page.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )

    # These fields are automatically set and should not be edited directly.
    # UserAdmin already makes these read-only, but it's good practice to be explicit.
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Improved admin configuration for the Profile model.
    """
    list_display = ('user_link', 'wallet', 'is_active_icon', 'invite_code', 'config_limitation', 'invited_by')
    list_filter = ('is_active', 'user__date_joined')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'invite_code', 'uuid')
    ordering = ('-user__date_joined',)
    
    autocomplete_fields = ('user', 'invited_by')

    fieldsets = (
        ('User Information', {'fields': ('user', 'is_active')}),
        ('Profile Details', {'fields': ('wallet', 'config_limitation', 'avatar')}),
        ('Invitation System', {'fields': ('uuid', 'invite_code', 'invited_by')}),
    )
    
    readonly_fields = ('uuid', 'invite_code')

    def user_link(self, obj):
        user_url = reverse('admin:accounts_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', user_url, obj.user.email)
    user_link.short_description = 'User Email'
    user_link.admin_order_field = 'user__email'

    def is_active_icon(self, obj):
        return boolean_icon(obj.is_active)
    is_active_icon.short_description = 'Profile Active'
    is_active_icon.admin_order_field = 'is_active'