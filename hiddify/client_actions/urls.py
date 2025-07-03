from django.urls import path
from . import views

urlpatterns = [
    path('addconfig/', views.AddConfigView, name='addconfig'),
    path('buynewconfig/', views.BuyNewConfigView, name='buynewconfig'),
    path('updateconfig/', views.AddOrderView, name='updateconfig'),
    path('deleteorder/', views.DeleteOrderView, name='deleteorder'),
    path('submit-payment/', views.PaymentView, name='submit-payment'),
    
    
    path('admin-panel/deleteorder/', views.DeleteOrderAdminView, name='deleteorderadmin'),
    path('admin-panel/confirmorder/', views.ConfirmOrderAdminView, name='confirmorderadmin'),
    
]
