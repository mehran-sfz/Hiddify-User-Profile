from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    
    # ------------ Login/Register ------------
    path('login-register/', views.LoginView, name='login_register'),
    path('login/', views.LoginView, name='login'),
    path('register/', views.LoginView, name='register'),
    path('logout/', views.LogoutView, name='logout'),
    
    # ------------ Admin Panel ------------
    path('admin-panel/', views.AdminPanelView, name='admin-panel'),
    path('admin-panel/home/', views.AdminPanelView, name='admin-panel'),
    path('admin-panel/orders/', views.AdminOrdersView, name='admin-panel-orders'),
    path('admin-panel/users/', views.AdminUsersView, name='admin-panel-users'),
    path('admin-panel/configs/', views.AdminConfigsView, name='admin-panel-configs'),
    path('admin-panel/plans/', views.AdminPlansView, name='admin-panel-plans'),
    path('admin-panel/logs/', views.AdminLogsView, name='admin-panel-logs'),
    path('admin-panel/messages/', views.AdminMessageView, name='admin-panel-messages'),
    
    
    # ------------ User Panel ------------
    path('', RedirectView.as_view(url='home/', permanent=False), name='root-redirect'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('orders/', views.OrdersView, name='orders'),
    path('buyconfig/', views.ByConfig, name='buyconfig'),
    path('addinvitecode/', views.AddinviteCodeView, name='addinvitecode'),
]
