# Generated by Django 4.1.7 on 2023-03-20 08:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phone_field.models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory_Management', '0002_alter_customuser_dob_alter_customuser_gender_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(max_length=150)),
                ('business_type', models.CharField(choices=[('MD', 'Medicine'), ('ST', 'Stationary'), ('GR', 'Grocery'), ('RS', 'Restaurant')], max_length=2, null=True)),
                ('business_address', models.CharField(max_length=300)),
                ('business_city', models.CharField(max_length=150)),
                ('business_state', models.CharField(max_length=150)),
                ('business_country', models.CharField(max_length=150)),
                ('business_phone', phone_field.models.PhoneField(help_text='Contact phone number', max_length=31, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
