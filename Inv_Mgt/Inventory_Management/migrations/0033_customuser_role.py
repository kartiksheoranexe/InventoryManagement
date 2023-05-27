# Generated by Django 4.1.5 on 2023-05-24 06:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Inventory_Management", "0032_businessworker"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[("owner", "Owner"), ("worker", "Worker")],
                default="worker",
                max_length=20,
            ),
        ),
    ]