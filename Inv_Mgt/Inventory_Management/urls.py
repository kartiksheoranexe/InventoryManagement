from django.urls import path
from Inventory_Management.views import CustomUserCreateAPIView, LoginAPIView, LogoutAPIView

urlpatterns = [
    path('register-user/', CustomUserCreateAPIView.as_view(), name='register'),
    path('login-user/', LoginAPIView.as_view(), name='login'),
    path('logout-user/', LogoutAPIView.as_view(), name='logout'),
   
]
