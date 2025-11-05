from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                 'is_staff', 'user_type', 'department', 'position', 'bio',
                 'profile_image', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'confirm_password', 
                 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user