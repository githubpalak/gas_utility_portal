# accounts/serializers.py
from rest_framework import serializers
from .models import UserProfile
from django.contrib.auth.password_validation import validate_password

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data
    """
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'phone_number', 'address', 'customer_id',
            'gas_meter_id', 'service_address'
        ]
        read_only_fields = ['role']  # Role can only be set by admin
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_password(self, value):
        validate_password(value)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = UserProfile.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class CustomerProfileSerializer(UserProfileSerializer):
    """
    Serializer specifically for customer accounts
    """
    class Meta(UserProfileSerializer.Meta):
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'phone_number', 'address', 'customer_id',
            'gas_meter_id', 'service_address'
        ]
    
    def create(self, validated_data):
        validated_data['role'] = UserProfile.CUSTOMER
        return super().create(validated_data)

class StaffProfileSerializer(UserProfileSerializer):
    """
    Serializer for support staff accounts
    """
    class Meta(UserProfileSerializer.Meta):
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'phone_number', 'employee_id', 'department'
        ]
    
    def create(self, validated_data):
        # Ensure role is one of the staff roles
        if validated_data.get('role') not in [UserProfile.SUPPORT_AGENT, UserProfile.MANAGER, UserProfile.ADMIN]:
            validated_data['role'] = UserProfile.SUPPORT_AGENT
        return super().create(validated_data)