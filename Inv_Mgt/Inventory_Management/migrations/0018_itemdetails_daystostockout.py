# Generated by Django 4.1.7 on 2023-04-21 07:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Inventory_Management", "0017_transaction_unit"),
    ]

    operations = [
        migrations.AddField(
            model_name="itemdetails",
            name="daystostockout",
            field=models.IntegerField(default=0),
        ),
    ]