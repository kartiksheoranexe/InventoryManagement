# Generated by Django 4.1.5 on 2023-05-02 12:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("Inventory_Management", "0023_remove_cartitem_cart_remove_cartitem_quantity"),
    ]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="cart",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.CASCADE,
                to="Inventory_Management.cart",
            ),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="quantity",
            field=models.PositiveIntegerField(default=0),
        ),
    ]