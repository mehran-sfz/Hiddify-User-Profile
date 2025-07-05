from django.contrib import admin

from .models import Config, Order, Payment


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['user', 'uuid', 'created_date']
    search_fields = ['uuid']
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'config', 'plan', 'status', 'pending' ,'created_date', 'updated_date']
    search_fields = ['user', 'config', 'plan']
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'config' ,'order', 'screenshot', 'validated', 'tracking_code', 'created_date', 'updated_date']
    search_fields = ['user', 'config', 'order']