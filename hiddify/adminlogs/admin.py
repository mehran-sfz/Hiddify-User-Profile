from django.contrib import admin
from .models import AdminLog, Message


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'date', 'status')
    list_filter = ('user', 'status')
    search_fields = ('action', 'user')
    ordering = ('-date',)
    

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'status')
    list_filter = ('status',)
    search_fields = ('title',)
    ordering = ('-date',)
