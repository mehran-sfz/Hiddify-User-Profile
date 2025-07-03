from django.contrib import admin
from .models import Plan, Bank_Information

@admin.register(Plan)
class UserAdmin(admin.ModelAdmin):
    list_display = ['trafic', 'location', 'duration', 'price', 'status']
    search_fields = ['trafic', 'location', 'duration', 'price']
    list_filter = ['status']
    ordering = ['-created_date']
    list_per_page = 20
    date_hierarchy = 'created_date' 
    fieldsets = (
        (None, {
            'fields': ('trafic', 'location', 'duration', 'price', 'status')
        }),
    )
    
    
@admin.register(Bank_Information)
class BankInformationAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'card_number', 'account_name', 'status']
    search_fields = ['bank_name', 'card_number', 'account_name']
    list_filter = ['status']
    ordering = ['-created_date']
    list_per_page = 20
    date_hierarchy = 'created_date'
    fieldsets = (
        (None, {
            'fields': ('bank_name', 'card_number', 'account_name', 'status')
        }),
    )