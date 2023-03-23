from rest_framework import serializers

from Inventory_Management.models import CustomUser, Business, Supplier, ItemDetails


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password',
                  'dob', 'gender', 'phone_no']
        extra_kwargs = {
            'password': {'write_only': True}
        }

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
    class Meta:
        model = ItemDetails
        fields = ['id', 'item_name', 'item_type', 'size', 'unit_of_measurement', 'quantity', 'additional_info']

class ItemDetailsSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer()

    class Meta:
        model = ItemDetails
        fields = ['id', 'supplier', 'item_name', 'item_type', 'size', 'unit_of_measurement', 'quantity', 'alert_quantity', 'additional_info', 'imported_date']