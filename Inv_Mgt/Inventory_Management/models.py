from django.db import models
from decimal import Decimal
from phone_field import PhoneField
from django.contrib.auth.models import AbstractUser

# Create your models here.
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

BUSINESS_TYPE = [
    ('Medicine', 'Medicine'),
    ('Stationary', 'Stationary'),
    ('Grocery', 'Grocery'),
    ('Restaurant', 'Restaurant'),
]

UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('gm', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
]

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    dob = models.DateField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    phone_no = PhoneField(help_text='Contact phone number', unique=True, null=True)

    def __str__(self):
        return self.username

class Business(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=150, unique=True)
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPE, null=True)
    business_address = models.CharField(max_length=300)
    business_city = models.CharField(max_length=150)
    business_state = models.CharField(max_length=150)
    business_country = models.CharField(max_length=150)
    business_phone = PhoneField(help_text='Contact phone number', null=True)
    business_email = models.EmailField(unique=True, null=True)

    def __str__(self):
        return self.owner.username + "-" + self.business_name

class Supplier(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    distributor_name = models.CharField(max_length=100)
    created_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['category', 'distributor_name'], name='unique_supplier')
        ]

    def __str__(self):
        return self.business.business_name + "-" + self.category + "-" + self.distributor_name

class ItemDetails(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=255)
    size = models.FloatField(default=0)
    unit_of_measurement = models.CharField(max_length=2, choices=UNIT_CHOICES)
    quantity = models.IntegerField(default=0)
    alert_quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cogs = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    additional_info = models.JSONField(blank=True, null=True)
    imported_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.supplier.category + "-" + self.supplier.distributor_name + "-" + self.item_name
    
class UpiDetails(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    payee_vpa = models.CharField(max_length=255)
    payee_name = models.CharField(max_length=255)
    merchant_code = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.payee_vpa}"

class Transaction(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    upi_details = models.ForeignKey(UpiDetails, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)
    transaction_ref_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item_id = models.IntegerField(default=0)
    unit = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.upi_details.user.username} - {self.transaction_id} - {self.status}"


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Cart"
    
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, default=0)
    item = models.ForeignKey(ItemDetails, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.item.item_name} - {self.quantity}"



