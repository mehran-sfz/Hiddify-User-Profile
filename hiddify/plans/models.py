from django.db import models


class Plan(models.Model):
    trafic = models.IntegerField(blank=False, null=False)
    location = models.CharField(max_length=100, default="Unknown", blank=True, null=True, verbose_name="Location")
    duration = models.IntegerField(blank=False, null=False, verbose_name="Duration in days")
    status = models.BooleanField(default=True, verbose_name="Active")
    price = models.IntegerField(blank=False, null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_datr = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'

    def __str__(self):
        return f"{self.trafic} گ، {self.duration} روز، {self.price} ت"

class Bank_Information(models.Model):
    bank_name = models.CharField(max_length=100, blank=False, null=False, verbose_name="Bank Name")
    card_number = models.CharField(max_length=100, blank=False, null=False, verbose_name="Card Number")
    account_name = models.CharField(max_length=100, blank=False, null=False, verbose_name="Account Name")
    status = models.BooleanField(default=True, verbose_name="Active")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)