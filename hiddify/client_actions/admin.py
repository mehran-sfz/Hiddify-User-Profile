# client_actions/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import Config, Order, Payment


# A helper function to display boolean values as icons
def boolean_icon(field_val):
    """
    Returns an HTML img tag for a boolean icon (yes/no checkmark).
    """
    icon_url = '/static/admin/img/icon-%s.svg' % ('yes' if field_val else 'no')
    return format_html('<img src="{}" alt="{}">', icon_url, field_val)

@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user_email', 'short_uuid', 'enabled_status', 'auto_extend_status', 'created_date')
    list_filter = ('enabled', 'auto_extend', 'created_date')
    search_fields = ('uuid', 'user__email')
    readonly_fields = ('created_date', 'updated_date')
    
    fieldsets = (
        ('Core Information', {
            'fields': ('user', 'uuid')
        }),
        ('Status and Settings', {
            'fields': ('enabled', 'auto_extend')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date')
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def short_uuid(self, obj):
        return f"{obj.uuid[:8]}...{obj.uuid[-8:]}" if obj.uuid else "-"
    short_uuid.short_description = 'UUID'

    def enabled_status(self, obj):
        return boolean_icon(obj.enabled)
    enabled_status.short_description = 'Enabled'

    def auto_extend_status(self, obj):
        return boolean_icon(obj.auto_extend)
    auto_extend_status.short_description = 'Auto Extend'

    actions = ['make_enabled', 'make_disabled']

    def make_enabled(self, request, queryset):
        queryset.update(enabled=True)
    make_enabled.short_description = "Enable selected configs"

    def make_disabled(self, request, queryset):
        queryset.update(enabled=False)
    make_disabled.short_description = "Disable selected configs"


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ('display_screenshot_in_admin', 'created_date', 'updated_date')
    fields = ('tracking_code', 'screenshot', 'display_screenshot_in_admin', 'validated', 'created_date', 'updated_date')

    def display_screenshot_in_admin(self, obj):
        if obj.screenshot:
            return format_html('<a href="{}"><img src="{}" width="150" /></a>', obj.screenshot.url, obj.screenshot.url)
        return "No screenshot available"
    display_screenshot_in_admin.short_description = 'Screenshot Preview'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # The *_link methods have been removed and replaced with direct field names.
    list_display = ('pk', 'user', 'config', 'plan', 'status_icon', 'pending_icon', 'created_date')
    list_filter = ('status', 'pending', 'plan', 'created_date')
    search_fields = ('user__email', 'config__uuid')
    readonly_fields = ('created_date', 'updated_date')
    autocomplete_fields = ['user', 'config']
    inlines = [PaymentInline]

    fieldsets = (
        (None, {
            'fields': ('user', 'config', 'plan')
        }),
        ('Order Status', {
            'fields': ('status', 'pending')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date')
        }),
    )

    def status_icon(self, obj):
        return boolean_icon(obj.status)
    status_icon.short_description = 'Status (Completed)'
    status_icon.admin_order_field = 'status'

    def pending_icon(self, obj):
        return boolean_icon(obj.pending)
    pending_icon.short_description = 'Pending'
    pending_icon.admin_order_field = 'pending'
    
    actions = ['mark_as_completed', 'mark_as_pending']

    def mark_as_completed(self, request, queryset):
        queryset.update(status=True, pending=False)
    mark_as_completed.short_description = "Mark selected orders as completed"

    def mark_as_pending(self, request, queryset):
        queryset.update(status=False, pending=True)
    mark_as_pending.short_description = "Return selected orders to pending"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # The 'order_link' method has been removed and replaced with the direct field 'order'.
    list_display = ('pk', 'order', 'user_email', 'validated_status', 'tracking_code', 'created_date')
    list_filter = ('validated', 'created_date')
    search_fields = ('user__email', 'config__uuid', 'order__id', 'tracking_code')
    readonly_fields = ('display_screenshot', 'created_date', 'updated_date')
    autocomplete_fields = ['user', 'config', 'order']

    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'user', 'config')
        }),
        ('Validation Details', {
            'fields': ('tracking_code', 'screenshot', 'display_screenshot', 'validated')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date')
        }),
    )

    def user_email(self, obj):
        return obj.user.email if obj.user else "N/A"
    user_email.short_description = 'User Email'

    def validated_status(self, obj):
        return boolean_icon(obj.validated)
    validated_status.short_description = 'Validated'
    validated_status.admin_order_field = 'validated'

    def display_screenshot(self, obj):
        if obj.screenshot:
            return format_html('<a href="{}"><img src="{}" style="max-height: 200px; max-width: 200px;" /></a>', obj.screenshot.url, obj.screenshot.url)
        return "No image provided"
    display_screenshot.short_description = 'Screenshot Preview'
    
    actions = ['validate_payments']

    def validate_payments(self, request, queryset):
        for payment in queryset:
            payment.validated = True
            payment.order.status = True
            payment.order.pending = False
            payment.save()
            payment.order.save()
    validate_payments.short_description = "Validate selected payments (and complete orders)"