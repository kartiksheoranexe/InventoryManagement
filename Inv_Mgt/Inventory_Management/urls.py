from django.urls import path
from Inventory_Management.views import CustomUserCreateAPIView, LoginAPIView, LogoutAPIView, BusinessCreateView, ListBusiness, SupplierCreateAPIView

urlpatterns = [
    path('register-user/', CustomUserCreateAPIView.as_view(), name='register'),
    path('login-user/', LoginAPIView.as_view(), name='login'),
    path('logout-user/', LogoutAPIView.as_view(), name='logout'),

    path('register_business/', BusinessCreateView.as_view(), name='register_business'),
    path('list_business/', ListBusiness.as_view(), name='list_business'),

    path('create_supplier/', SupplierCreateAPIView.as_view(), name='create_supplier'),
    # path('del_suppliers/', SupplierDeleteAPIView.as_view(), name='supplier_delete'),
    # path('all_suppliers/', ListSupplier.as_view(), name='suppliers_list'),
    # path('suppliers/', SearchSupplierAPIView.as_view(), name='suppliers-list'),

]
