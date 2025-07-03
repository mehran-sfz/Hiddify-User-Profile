from django.db import models
from datetime import timedelta

class HiddifyUser(models.Model):
    
    added_by_uuid = models.CharField(max_length=256, blank=True, null=True)
    current_usage_GB = models.FloatField(blank=True, null=True, default=0.0)
    enable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    last_online = models.TimeField(blank=True, null=True)
    last_reset_time = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    package_days = models.IntegerField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    telegram_id = models.CharField(max_length=256, blank=True, null=True)
    usage_limit_GB = models.FloatField(blank=True, null=True, default=0.0)
    uuid = models.CharField(max_length=256, blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'HiddifyUser'
        verbose_name_plural = 'HiddifyUsers'
        
        
    def save(self, *args, **kwargs):
        # Check if start_date and package_days are set before calculating end_date
        if self.start_date and self.package_days is not None:
            self.end_date = self.start_date + timedelta(days=self.package_days)
        else:
            self.end_date = None  # Set end_date to None if required fields are not available
            
        super().save(*args, **kwargs)  # Call the parent save method

    def __str__(self):
        return self.uuid
    

class HiddifyAccessInfo(models.Model):
    hiddify_api_key = models.CharField(max_length=256, blank=True, null=True)
    admin_proxy_path = models.CharField(max_length=256, blank=True, null=True)
    panel_admin_domain = models.CharField(max_length=256, blank=True, null=True)
    sub_proxy_path = models.CharField(max_length=256, blank=True, null=True)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.panel_admin_domain
