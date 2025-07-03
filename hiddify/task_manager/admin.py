from django.contrib import admin
from .models import HiddifyUser, HiddifyAccessInfo


@admin.register(HiddifyUser)
class HiddifyUserAdmin(admin.ModelAdmin):
    list_display = ['name', 'uuid', 'package_days', 'start_date', 'end_date', 'usage_limit_GB', 'enable']

@admin.register(HiddifyAccessInfo)
class HiddifyAccessInfo(admin.ModelAdmin):
    list_display = ['hiddify_api_key', 'admin_proxy_path', 'panel_admin_domain', 'sub_proxy_path']