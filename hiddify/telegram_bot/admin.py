from django.contrib import admin

from .models import Telegram_account, Telegram_Bot_Info


@admin.register(Telegram_Bot_Info)
class Telegram_Bot_Info_Admin(admin.ModelAdmin):
    list_display = ('site_domain', 'token', 'bot_name', 'created_date', 'updated_date')


@admin.register(Telegram_account)
class Telegram_account_Admin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'telegram_user_id', 'username', 'created_date', 'updated_date')

