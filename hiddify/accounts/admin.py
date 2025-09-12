# accounts/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import CustomUser, Profile


# A helper function to display boolean values as icons
def boolean_icon(field_val):
    icon_url = f"/static/admin/img/icon-{'yes' if field_val else 'no'}.svg"
    return format_html('<img src="{}" alt="{}">', icon_url, field_val)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Simplified admin configuration for the CustomUser model.
    """
    list_display = ('email', 'first_name', 'last_name', 'is_active_icon', 'is_staff_icon', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Simplified fieldsets without BaseUserAdmin's complexities
    fieldsets = (
        ('User Info', {'fields': ('email', 'first_name', 'last_name')}),
        ('Status', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        # Password field is made read-only to prevent incorrect saving
        ('Security', {'fields': ('password',)}),
        ('Important Dates', {'fields': ('date_joined', 'last_login')}),
    )

    # Make password and auto-dates read-only
    readonly_fields = ('password', 'date_joined', 'last_login')

    def is_active_icon(self, obj):
        return boolean_icon(obj.is_active)
    is_active_icon.short_description = 'Active'

    def is_staff_icon(self, obj):
        return boolean_icon(obj.is_staff)
    is_staff_icon.short_description = 'Staff'

# -----------------------------------------------------------------
# The ProfileAdmin class remains unchanged as it was correct.
# -----------------------------------------------------------------

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