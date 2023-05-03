# Generated by Django 4.1.5 on 2023-05-02 12:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("Inventory_Management", "0021_cartitem_cart"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cart",
            name="items",
        ),
        migrations.AddField(
            model_name="cartitem",
            name="cart",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.CASCADE,
                to="Inventory_Management.cart",
            ),
            preserve_default=False,
        ),
    ]