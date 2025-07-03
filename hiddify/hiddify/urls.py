"""
URL configuration for hiddify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    
    # --------------------- Admin URLs ----------------
    path('admin/', admin.site.urls),

    # --------------------- API URLs ----------------
    path('api/', include('api.urls')), # include the urls of the api app
    
    # --------------------- Frontend URLs ----------------
    path('', include('accounts.urls')),
    path('', include('client_actions.urls')),
    
    # --------------------- Plans URLs ----------------
    path('', include('plans.urls')),
    
    # --------------------- Telegram Bot URLs ----------------
    path('telegram-bot/', include('telegram_bot.urls')),
    
    # --------------------- Admin Logs URLs ----------------
    path('', include('adminlogs.urls')),
    
]

if settings.IS_DEVELOPMENT:
    urlpatterns += static('/media', document_root=settings.MEDIA_ROOT)
