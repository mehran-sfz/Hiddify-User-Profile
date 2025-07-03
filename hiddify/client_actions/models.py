from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from task_manager.models import HiddifyUser
from plans.models import Plan


class Config(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='config')
    uuid = models.CharField(max_length=256 ,blank=False, null=False, unique=True)
    auto_extend = models.BooleanField(default=False) #TODO: Implement auto extend logic
    enabled = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Config'
        verbose_name_plural = 'Configs'
        
    def save(self, *args, **kwargs):
        # Check if a HiddifyUser exists with added_by_uuid equal to the Config's uuid
        if not HiddifyUser.objects.filter(uuid=self.uuid).exists():
            raise ValidationError(f"No HiddifyUser with added_by_uuid matching uuid {self.uuid}.")
        
        self.uuid = self.uuid.strip()
        
        # Proceed with saving if the condition is met
        super(Config, self).save(*args, **kwargs)

    def __str__(self):
        return self.uuid
    
class Order(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='orders', null=True, blank=False)
    config = models.ForeignKey(to=Config, on_delete=models.SET_NULL, null=True, blank=False, related_name='order_configs')
    plan = models.ForeignKey(to=Plan, on_delete=models.SET_NULL, null=True, blank=False, related_name='order_plans')
    status = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"{self.config} - {self.plan}"
    
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='user_payments', null=True, blank=False)
    config = models.ForeignKey(Config, on_delete=models.SET_NULL, null=True, blank=False, related_name='config_payments')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=False, blank=False, related_name='order_payment')
    screenshot = models.ImageField(upload_to='screenshots/%Y/%m/%d/', blank=True, null=True)
    tracking_code = models.CharField(max_length=256, blank=True, null=True)
    validated = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment'
        verbose_name = 'payment'
        verbose_name_plural = 'payments'

    def __str__(self):
        return f"User {self.user} - validated: {'Paid' if self.validated else 'Pending'}"
