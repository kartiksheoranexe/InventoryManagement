from django.db import models
from phone_field import PhoneField
from django.contrib.auth.models import AbstractUser

# Create your models here.
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

BUSINESS_TYPE = [
    ('MD', 'Medicine'),
    ('ST', 'Stationary'),
    ('GR', 'Grocery'),
    ('RS', 'Restaurant'),
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
    business_type = models.CharField(max_length=2, choices=BUSINESS_TYPE, null=True)
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
    additional_info = models.JSONField(blank=True, null=True)
    imported_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.supplier.category + "-" + self.supplier.distributor_name + "-" + self.item_name

