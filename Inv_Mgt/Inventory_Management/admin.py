from django.contrib import admin
from Inventory_Management.models import CustomUser, Business, Supplier

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'phone_no', 'dob', 'gender']

class BusinessAdmin(admin.ModelAdmin):
    list_display = ['owner', 'business_name', 'business_type']

class SupplierAdmin(admin.ModelAdmin):
    list_display = ['business', 'category', 'distributor_name', 'created_date']

admin.site.register(CustomUser, CustomUserAdmin),
admin.site.register(Business, BusinessAdmin),
admin.site.register(Supplier, SupplierAdmin),
