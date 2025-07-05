
from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import (ConfigListView, ConfigView, OrderListView, OrderView,
                    PaymentListView, PaymentView, PlanlisrView, ProfileView,
                    RegisterView)

urlpatterns = [
    
    path('profile/', ProfileView.as_view(), name='profile'),
    
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('configlist/', ConfigListView.as_view(), name='config-list'),
    path('config/', ConfigView.as_view(), name='create-config'),
    
    path('orderlist/', OrderListView.as_view(), name='order-list'),
    path('order/', OrderView.as_view(), name='create-order'),
    
    path('paymentlist/', PaymentListView.as_view(), name='payment-list'),
    path('payment/', PaymentView.as_view(), name='create-payment'),
    
    path('planlist/', PlanlisrView.as_view(), name='planlist'),
]
 