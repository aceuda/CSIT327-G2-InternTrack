from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude =  ['is_deleted', 'is_superuser', 'last_login', 'groups', 'user_permissions', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validate_data):
        password = validate_data.pop('password')
        return User.objects.create_user(password = password, **validate_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
class UserSerializer(serializers.ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = "__all__" 

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Used for serialization of our jwt token
    """
    username_field = 'username'
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['id'] = user.id
        token['user_type'] = user.user_type
        token['username'] = user.username
        return token