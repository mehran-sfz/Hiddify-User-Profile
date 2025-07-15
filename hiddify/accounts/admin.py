from django.contrib import admin

from .models import CustomUser, Profile


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'user_date_joined']
    
    
    # Method to display the date the user joined
    def user_date_joined(self, user):
        return user.date_joined.strftime('%Y-%m-%d')
    user_date_joined.short_description = 'Date Joined'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'user_first_name', 'user_last_name', 'wallet', 'invited_by', 'invite_code', 'config_limitation' ,'user_date_joined']

    # Method to display the user's Email
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    # Method to display if the user is active
    def user_first_name(self, obj):
        return obj.user.first_name
    
    user_first_name.short_description = 'First Name'
    
    # Method to display if the user is active
    def user_last_name(self, obj):
        return obj.user.last_name
    
    user_last_name.short_description = 'Last Name'

    # Method to display the date the user joined
    def user_date_joined(self, obj):
        return obj.user.date_joined.strftime('%Y-%m-%d')
    user_date_joined.short_description = 'Date Joined'
    


