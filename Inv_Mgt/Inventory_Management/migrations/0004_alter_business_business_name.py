# Generated by Django 4.1.7 on 2023-03-20 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory_Management', '0003_business'),
    ]

    operations = [
        migrations.AlterField(
            model_name='business',
            name='business_name',
            field=models.CharField(max_length=150, unique=True),
        ),
    ]
