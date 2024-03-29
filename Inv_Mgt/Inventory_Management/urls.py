from django.urls import path
from Inventory_Management.views import CustomUserCreateAPIView, LoginAPIView, LogoutAPIView, BusinessCreateView, ListBusiness, SupplierCreateAPIView,\
    SupplierUpdateAPIView, SupplierDeleteAPIView, ListBusinessSuppliers, SearchSupplierAPIView, ItemDetailsListAPIView, ItemDetailsCreateAPIView, \
    SearchItemDetailsAPIView, ItemAlertListAPIView, ItemAlertCountAPIView, GenerateQRCodeAPIView, UpdateItemQuantityAPIView, ImportExcelDataAPIView, \
    UpdateTransactionStatusAPIView, CreateUpiDetailsAPIView, TransactionsByDateView, SalesPerformanceAPIView, TopItemsAPIView, CartItemListCreateAPIView, \
    CartItemRetrieveUpdateDestroyAPIView,ListUPIDetails,UPIDeleteAPIView, PasswordResetRequestCreateAPIView, VerifyOTPAPIView, ResetPasswordAPIView, \
    ItemDetailsUpdateDeleteView, CartItemCountAPIView, CurrentUserAPIView, UpdateUserAPIView, BusinessWorkerCreateAPIView, HelloWorldView

urlpatterns = [
    path('register-user/', CustomUserCreateAPIView.as_view(), name='register'),
    path('login-user/', LoginAPIView.as_view(), name='login'),
    path('logout-user/', LogoutAPIView.as_view(), name='logout'),
    path('password-reset-request/', PasswordResetRequestCreateAPIView.as_view(), name='password_reset_request'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify_otp'),
    path('password-reset/', ResetPasswordAPIView.as_view(), name='reset_password'),
    path('user/', CurrentUserAPIView.as_view(), name='current_user'),
    path('user/update/', UpdateUserAPIView.as_view(), name='update_user'),

    path('register_business/', BusinessCreateView.as_view(), name='register_business'),
    path('list_business/', ListBusiness.as_view(), name='list_business'),
    path('register-worker/', BusinessWorkerCreateAPIView.as_view(), name='register-worker'),

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
    path('item/update_delete/', ItemDetailsUpdateDeleteView.as_view(), name='item_update_delete'),
    
    path('register-your-upi/', CreateUpiDetailsAPIView.as_view()),
    path('list_upi_details/', ListUPIDetails.as_view(), name='list_upi_details'),
    path('del_upi_details/', UPIDeleteAPIView.as_view(), name='del_upi'),
    path('generate-qr-code/', GenerateQRCodeAPIView.as_view()),
    path('modify-item-quantity/', UpdateItemQuantityAPIView.as_view()),
    path('update-transaction-status/', UpdateTransactionStatusAPIView.as_view()),
    path('transaction-details/', TransactionsByDateView.as_view()),
    
    path('sales-performance/', SalesPerformanceAPIView.as_view()),
    path('top-items/', TopItemsAPIView.as_view(), name='top-items'),

    path('import-item-excel/', ImportExcelDataAPIView.as_view()),

    path('cart/', CartItemListCreateAPIView.as_view(), name='cart-list-create'),
    path('cart/<int:pk>/', CartItemRetrieveUpdateDestroyAPIView.as_view(), name='cart-item-detail'),
    path('cart-item-count/', CartItemCountAPIView.as_view(), name='cart-count-detail'),

    # path('ocr/', OCRAPIView.as_view(), name='ocr'),
    path('hello/', HelloWorldView.as_view(), name='hello'),


]
