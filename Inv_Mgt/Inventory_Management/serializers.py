from rest_framework import serializers
from django.utils import timezone
from datetime import date
import math

from Inventory_Management.models import CustomUser, PasswordResetRequest, Business, Supplier, ItemDetails, UpiDetails, Transaction, CartItem


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password',
                  'dob', 'gender', 'phone_no']
        extra_kwargs = {
            'password': {'write_only': True}
        }

def validate_username(self, value):
        if ' ' in value:
            raise serializers.ValidationError("Username must not contain spaces.")
        return value

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordResetRequest
        fields = ['user', 'otp', 'timestamp', 'is_used']

class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ('business_name', 'business_type', 'business_address',
                  'business_city', 'business_state', 'business_country', 'business_phone', 'business_email')

class SupplierSerializer(serializers.ModelSerializer):
    business = BusinessSerializer() 

    class Meta:
        model = Supplier
        fields = ('business', 'category', 'distributor_name')

class ItemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemDetails
        fields = '__all__'

class ItemDetailsSearchSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer()
    daystostockout = serializers.SerializerMethodField()

    class Meta:
        model = ItemDetails
        fields = ['id', 'item_name', 'item_type', 'size', 'unit_of_measurement', 'quantity', 'price', 'cogs', 'additional_info', 'daystostockout', 'alert_quantity', 'supplier']

    def get_daystostockout(self, obj):
        today = date.today()
        transactions_today = Transaction.objects.filter(item_id=obj.id, created_at__date=today, status='success')
        total_units_sold = sum(transaction.unit for transaction in transactions_today)

        if total_units_sold > 0:
            d_daystostockout = obj.quantity / total_units_sold
            daystostockout = math.ceil(d_daystostockout)
            return daystostockout
        else:
            daystostockout = 0
            return daystostockout

class ItemDetailAlertSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer()

    class Meta:
        model = ItemDetails
        fields = ['id', 'supplier', 'item_name', 'item_type', 'size', 'unit_of_measurement', 'quantity', 'alert_quantity', 'additional_info', 'imported_date']

class UpiDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpiDetails
        fields = ['payee_vpa', 'payee_name', 'merchant_code', 'url']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'upi_details', 'transaction_id', 'transaction_ref_id',
            'amount', 'item_id', 'unit', 'status', 'created_at', 'updated_at'
        ]

class TransactionDetailsSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    item_details = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ('time', 'unit', 'amount', 'status', 'transaction_id', 'item_details')
        depth = 1

    def get_time(self, obj):
        local_time = timezone.localtime(obj.created_at)
        return local_time.time()

    def get_item_details(self, obj):
        item = ItemDetails.objects.get(id=obj.item_id)
        return ItemDetailsSerializer(item).data

class CartItemSerializer(serializers.ModelSerializer):
    item = ItemDetailsSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'quantity']