from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AdminProfile, StudentProfile, User
#Serializes the User model for API registration/login
#bridge between our database models and API endpoints
#Base logic for user create/update, handles password hashing

#This handles the base logic for user creation and update.
class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude =  ['is_deleted', 'is_superuser', 'last_login', 'groups', 'user_permissions', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    #handles creating new object
    def create(self, validate_data):
        password = validate_data.pop('password')
        return User.objects.create_user(password = password, **validate_data)
    
    #updates user info
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

  #exposing all fields  
class UserSerializer(serializers.ModelSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = "__all__" 

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = StudentProfile
        fields = ['user', 'student_id', 'program']

    def create(self, validated_data):
        # Extract nested user data
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = StudentProfile.objects.create(user=user, **validated_data)
        return student

class AdminDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = AdminProfile
        fields = ['user', 'department', 'position']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        admin = AdminProfile.objects.create(user=user, **validated_data)
        return admin

#Authentication (login token generation)
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