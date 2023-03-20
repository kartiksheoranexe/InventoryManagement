from django.contrib import admin
from Inventory_Management.models import CustomUser

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'phone_no', 'dob', 'gender']

admin.site.register(CustomUser, CustomUserAdmin),
