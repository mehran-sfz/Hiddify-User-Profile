from .models import AdminLog


def add_admin_log(action, category , user):
    
    try:
        log = AdminLog.objects.create(action=action, category=category, user=user)
        return log.pk
    except Exception as e:
        return False