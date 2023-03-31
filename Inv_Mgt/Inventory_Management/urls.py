from django.urls import path
from Inventory_Management.views import CustomUserCreateAPIView, LoginAPIView, LogoutAPIView, BusinessCreateView, ListBusiness, SupplierCreateAPIView, SupplierUpdateAPIView, SupplierDeleteAPIView, ListBusinessSuppliers, SearchSupplierAPIView, ItemDetailsListAPIView, ItemDetailsCreateAPIView, SearchItemDetailsAPIView, ItemAlertListAPIView, ItemAlertCountAPIView, UpdateItemQuantityAPIView, ImportExcelDataAPIView

urlpatterns = [
    path('register-user/', CustomUserCreateAPIView.as_view(), name='register'),
    path('login-user/', LoginAPIView.as_view(), name='login'),
    path('logout-user/', LogoutAPIView.as_view(), name='logout'),

    path('register_business/', BusinessCreateView.as_view(), name='register_business'),
    path('list_business/', ListBusiness.as_view(), name='list_business'),

    path('create_supplier/', SupplierCreateAPIView.as_view(), name='create_supplier'),
    path('update_supplier/', SupplierUpdateAPIView.as_view(), name='update_supplier'),
    path('del_suppliers/', SupplierDeleteAPIView.as_view(), name='supplier_delete'),
    path('all_suppliers/', ListBusinessSuppliers.as_view(), name='suppliers_list'),
    path('suppliers/', SearchSupplierAPIView.as_view(), name='suppliers-list'),

    path('items/', ItemDetailsListAPIView.as_view()),
    path('add-item/', ItemDetailsCreateAPIView.as_view(), name='create_item_info'),
    path('search-items/', SearchItemDetailsAPIView.as_view()),
    path('raise-alert/', ItemAlertListAPIView.as_view()),
    path('alert-count/', ItemAlertCountAPIView.as_view()),
    
    path('modify-item-quantity/', UpdateItemQuantityAPIView.as_view()),

    path('import-item-excel/', ImportExcelDataAPIView.as_view()),

]
