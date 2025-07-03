from django.db import models

# log for admin


class AdminLog(models.Model):

    ACTION_CATEGORIES = [
            ('not_categorized', 'Not Categorized'),  # Default category
            ('user', 'User'),
            ('admin', 'Admin'),
            ('system', 'System'),
            ('add user', 'Add User'),
        ]

    action = models.CharField(max_length=1024)
    user = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)
    category = models.CharField(max_length=15, choices=ACTION_CATEGORIES, default='not_categorized')

    class Meta:
        db_table = 'adminlogs'
        verbose_name = 'Admin Log'
        verbose_name_plural = 'Admin Logs'

    def __str__(self):
        return f"{self.action} by {self.user} at {self.date}"


# A message that shown to the users
class Message(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return self.title