from django.urls import path

from . import views

urlpatterns = [
    
    # ------------ Admin Panel ------------
    path('admin-panel/add-message/', views.SendMessageToAll, name='send-message-to-all'),
    path('admin-panel/active-message/<int:pk>/', views.DeactiveMessage, name='admin-message-active'),

]
