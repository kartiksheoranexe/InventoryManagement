from django.urls import path
from Inventory_Management.views import CustomUserCreateAPIView

urlpatterns = [
    path('register-user/', CustomUserCreateAPIView.as_view(), name='register'),
   
]
