from django.contrib.auth.models import AbstractUser
from phone_field import PhoneField

from django.db import models

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
        return self.business.business_name + "-" + self.distributor_name
