from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Sum

from .models import AdminProfile, StudentProfile, User, Attendance, Report
#Serializes the User model for API registration/login
#bridge between our database models and API endpoints
#Base logic for user create/update, handles password hashing

#This handles the base logic for user creation and update.
class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude =  ['is_deleted', 'is_superuser', 'last_login', 'groups', 'user_permissions', 'is_active', 'is_staff']
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
    
class StudentProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(max_length=None, use_url=True,required=False)
    total_rendered_hours = serializers.SerializerMethodField()
    class Meta:
        model = StudentProfile
        fields = ['id', 'full_name', 'year_level', 'program', 'student_id', 'profile_image','company','address', 'total_rendered_hours']
        read_only_fields = ['full_name', 'company']

    def get_total_rendered_hours(self, obj):
        total_h = Attendance.objects.filter(student__id=obj.id).aggregate(
            total = Sum('hours_rendered')
        )['total']
        return float(total_h) if total_h is not None else 0.0
class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = ['full_name', 'department', 'position', 'employee_id', 'profile_image', 'company', 'address']
        read_only_fields = ['full_name', 'company']
        

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

class AttendanceSerializer(serializers.ModelSerializer):
    # Optionally, you can add nested serializers if you want to include related data, like student info
    student_name = serializers.CharField(source='student.full_name')  # Adding student name for readability

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'date', 'time_in', 'time_out', 'hours_rendered']
        read_only_fields = ['id', 'student', 'student_name'] 

class ReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'student', 'student_name', 'title', 'summary', 'submitted_at']
        read_only_fields = ['submitted_at'] 