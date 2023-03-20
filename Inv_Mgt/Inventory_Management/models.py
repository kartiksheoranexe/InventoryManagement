from django.contrib.auth.models import AbstractUser
from phone_field import PhoneField

from django.db import models

# Create your models here.
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    dob = models.DateField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    phone_no = PhoneField(help_text='Contact phone number', unique=True, null=True)