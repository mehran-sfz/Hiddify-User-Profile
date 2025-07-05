import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------- environment variables ----------------------

# Load environment variables from .env file
DEBUG = True if os.environ.get('DEBUG') == 'True' else False
IS_DEVELOPMENT = True if os.environ.get('IS_DEVELOPMENT') == 'True' else False
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key').strip()
ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOSTS', '*').strip()]

IS_HTTPS_USED = True if os.environ.get('IS_HTTPS_USED') == 'True' else False
if IS_HTTPS_USED and ALLOWED_HOSTS != ['*']:
    CSRF_COOKIE_SECURE = True if os.environ.get('CSRF_COOKIE_SECURE') == 'True' else False
    SESSION_COOKIE_SECURE = True if os.environ.get('SESSION_COOKIE_SECURE') == 'True' else False
    CSRF_TRUSTED_ORIGINS = ['https://'+ host.strip() for host in ALLOWED_HOSTS if host.strip() != '*']
    

# duration for different tasks
WAITING_FOR_PAYMENT_TIMEOUT_DAYS = int(os.environ.get('WAITING_FOR_PAYMENT_TIMEOUT_DAYS', 5))
WARNING_FOR_PAYMENT_TIMEOUT_DAYS = int(os.environ.get('WARNING_FOR_PAYMENT_TIMEOUT_DAYS', 3))
WARNING_FOR_CONFIG_TIMEOUT_DAYS = int(os.environ.get('WARNING_FOR_CONFIG_TIMEOUT_DAYS', 5))
WARNING_FOR_USAGE_GB = int(os.environ.get('WARNING_FOR_USAGE_GB', 5))
FETCH_USERS_DURATION_SECONDS = int(os.environ.get('FETCH_USERS_DURATION_SECONDS', 120))
TELEGRAM_NOTIFICATION_INTERVAL_HOURS = int(os.environ.get('TELEGRAM_NOTIFICATION_INTERVAL_HOURS', 12))

# information of your telegram channel
if ALLOWED_HOSTS != ['*']:
    DOMAIN_NAME = f'https://{ALLOWED_HOSTS[0]}'
else:
    DOMAIN_NAME = 'https://t.me/batmanam2'
    
CHANNEL_NAME= os.environ.get('CHANNEL_NAME', 'Batmanam')
CHANNEL_LINK= os.environ.get('CHANNEL_LINK', 'https://t.me/batmanam_v')  
SUPPORT_TELEGRAM_LINK= os.environ.get('SUPPORT_TELEGRAM_LINK', 'https://t.me/batmanam2')


# ---------------------- end of environment variables ----------------------


# CSRF life time
CSRF_COOKIE_AGE = 86400


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'rest_framework_simplejwt',
    
    'accounts',
    'client_actions',
    'plans',
    
    'api',
    'telegram_bot',
    
    'task_manager',
    'adminlogs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hiddify.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hiddify.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME'  : os.environ.get('DATABASE_NAME', 'postgres'),
        'USER'  : os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD'  : os.environ.get('DATABASE_PASSWORD', 'postgres'),
        'HOST'  : os.environ.get('DATABASE_HOST', 'database'),
        'PORT'  : os.environ.get('DATABASE_PORT', '5432'),
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
# You can still have STATICFILES_DIRS for development purposes
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'accounts/static'),] # Add the accounts app static files directory to the list

STATIC_ROOT = BASE_DIR / 'static' 
MEDIA_ROOT = BASE_DIR / 'media' 



# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Tell Django to use the CustomUser model for authentication
AUTH_USER_MODEL = 'accounts.CustomUser'


# ----------------- REST Framework settings -----------------
REST_FRAMEWORK = {
    
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    
}

# ----------------- Celery settings -----------------

# Celery settings
CELERY_BEAT_SCHEDULE = {
    'fetch-data-from-hiddify-api': {
        'task': 'task_manager.tasks.fetch_data_from_api',
        'schedule': timedelta(seconds=FETCH_USERS_DURATION_SECONDS),  # Executes every 1 minutes
    },
    
    'check-subscription-expiry': {
        'task': 'task_manager.tasks.check_subscription_expiry',
        'schedule': timedelta(seconds=FETCH_USERS_DURATION_SECONDS),  # Executes every 2 hours   
    },
    
    'disable-not-paid-users' : {
        'task': 'task_manager.tasks.disable_not_paid_users',
        'schedule': timedelta(hours=TELEGRAM_NOTIFICATION_INTERVAL_HOURS),
    },
    
    'send-telegram-notification-to-unpayed-users': {
        'task': 'task_manager.tasks.send_payment_reminder_messsage',
        'schedule': timedelta(hours=TELEGRAM_NOTIFICATION_INTERVAL_HOURS),
    },
    'send-telegram-warning-to-expired-users': {
        'task': 'task_manager.tasks.send_warning_message',
        'schedule': timedelta(hours=TELEGRAM_NOTIFICATION_INTERVAL_HOURS),
    },
}
