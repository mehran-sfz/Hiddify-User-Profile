from django.urls import path

from . import views

urlpatterns = [
    
    # User Authentication URLs
    path('addconfig/', views.AddConfigView, name='addconfig'),
    path('buynewconfig/', views.BuyNewConfigView, name='buynewconfig'),
    path('updateconfig/', views.AddOrderView, name='updateconfig'),
    path('deleteorder/', views.DeleteOrderView, name='deleteorder'),
    path('submit-payment/', views.PaymentView, name='submit-payment'),
    
    
    # Admin Panel URLs
    path('admin-panel/deleteorder/', views.DeleteOrderAdminView, name='deleteorderadmin'),
    path('admin-panel/confirmorder/', views.ConfirmOrderAdminView, name='confirmorderadmin'),
    
    # Payment Screenshot URLs
    path('payment-screenshot/<int:payment_id>/', views.serve_payment_screenshot, name='serve_payment_screenshot'),

    
]
