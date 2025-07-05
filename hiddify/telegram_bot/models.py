from django.conf import settings
from django.db import models

from accounts.models import Profile


class Telegram_Bot_Info(models.Model):
    site_domain = models.CharField(max_length=256)
    token = models.CharField(max_length=256)
    bot_name = models.CharField(max_length=256)
    admin_user_id = models.CharField(max_length=256, blank=True, null=True)
    created_date =  models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.bot_name


class Telegram_account(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_account')    
    first_name = models.CharField(max_length=256, blank=True, null=True)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    telegram_user_id = models.CharField(max_length=256, unique=True)
    username = models.CharField(max_length=256, blank=True, null=True)
    created_date =  models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
