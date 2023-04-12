from django.contrib import admin
from Inventory_Management.models import CustomUser, Business, Supplier, ItemDetails, UpiDetails, Transaction

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'phone_no', 'dob', 'gender']

class BusinessAdmin(admin.ModelAdmin):
    list_display = ['owner', 'business_name', 'business_type']

class SupplierAdmin(admin.ModelAdmin):
    list_display = ['business', 'category', 'distributor_name', 'created_date']

class ItemDetailsAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'item_name', 'item_type', 'created_at']

admin.site.register(CustomUser, CustomUserAdmin),
admin.site.register(Business, BusinessAdmin),
admin.site.register(Supplier, SupplierAdmin),
admin.site.register(ItemDetails, ItemDetailsAdmin),
admin.site.register(UpiDetails),
admin.site.register(Transaction),
