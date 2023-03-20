from rest_framework import serializers

from Inventory_Management.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password',
                  'dob', 'gender', 'phone_no']
        extra_kwargs = {
            'password': {'write_only': True}
        }