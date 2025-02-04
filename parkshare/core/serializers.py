# serializers.py
import re
from rest_framework import serializers
from .models import CustomUser
from rest_framework.exceptions import ValidationError

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'password', 'confirm_password', 'role']

    def validate(self, data):
        """
        Custom validation for passwords.
        - Ensures passwords match.
        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Ensure passwords match
        if password != confirm_password:
            raise ValidationError({"confirm_password": "Passwords do not match."})
        # Ensure password is at least 8 characters long
        if len(password) < 8:
            raise ValidationError({"password": "Password must be at least 8 characters long."})

        # Ensure password contains at least one letter and one number
        if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            raise ValidationError({"password": "Password must contain at least one letter and one number."})

        # Ensure password contains at least one special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError({"password": "Password must contain at least one special character."})

        return data

    def create(self, validated_data):
        # Create the new user with validated data
        user = CustomUser(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number']
        )
        user.set_password(validated_data['password'])  # Hash password
        user.role = validated_data.get('role', [])  # Assign roles
        user.save()

        return user