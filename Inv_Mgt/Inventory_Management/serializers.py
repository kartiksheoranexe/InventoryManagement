from rest_framework import serializers

from Inventory_Management.models import CustomUser, Business, Supplier


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
                  'business_city', 'business_state', 'business_country', 'business_phone')

class SupplierSerializer(serializers.ModelSerializer):
    business = BusinessSerializer()

    class Meta:
        model = Supplier
        fields = ('business', 'category', 'distributor_name')
        