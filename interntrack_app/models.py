
import uuid
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone


#Interact with the database (create/authenticate users)
#Model for tracking intern progress
class Intern(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    hours_completed = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
#Role options
class UserRoles(models.TextChoices):
    """
    Create/Modify user roles here
    Add role in the same format (CUSTOM_ROLE = 'custom_role', 'Custom Role')
    """
    ADMIN = 'supervisor', 'Admin'
    STUDENT = 'student', 'Student'

#Handles how users are created, both normal users and superusers.
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("user_type", UserRoles.ADMIN)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthdate = models.DateField(null=False)
    #year_level = models.IntegerField(null=False)
    email = models.CharField(max_length=100)
    user_type = models.CharField(choices=UserRoles, default=UserRoles.STUDENT)
    username = models.CharField(unique=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=150, blank=True) 
    year_level = models.IntegerField(null=False)
    program = models.CharField(max_length=100, null=False)
    student_id = models.CharField(max_length=12, null=False, unique=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True) 
    completed_hours = models.PositiveIntegerField(default=0)
    # New DB field

    def save(self, *args, **kwargs):
        self.full_name = f"{self.user.first_name} {self.user.last_name}"
        super().save(*args, **kwargs)

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=150, blank=True) 
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True) 

    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            raw_id = uuid.uuid4().hex[:6].upper()
            self.employee_id = f"ADM-{raw_id}"
        else:
            # Normalize manually entered ID
            cleaned = self.employee_id.replace(" ", "").upper()
            if not cleaned.startswith("ADM-"):
                cleaned = f"ADM-{cleaned}"
            self.employee_id = cleaned

        self.full_name = f"{self.user.first_name} {self.user.last_name}"
        super().save(*args, **kwargs)

class Attendance(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)  # Use localdate for just date
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    hours_rendered = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def calculate_hours(self):
        if self.time_in and self.time_out:
            # Combine date + time into timezone-aware datetimes
            in_dt = timezone.make_aware(datetime.combine(self.date, self.time_in), timezone.get_current_timezone())
            out_dt = timezone.make_aware(datetime.combine(self.date, self.time_out), timezone.get_current_timezone())

            # Handle if time_out is past midnight (next day)
            if out_dt < in_dt:
                out_dt += timedelta(days=1)

            delta = out_dt - in_dt
            self.hours_rendered = round(delta.total_seconds() / 3600, 2)
            self.save()

    def __str__(self):
        return f"{self.student.full_name} - {self.date}"

#Evaluation
class Evaluation(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    remarks = models.TextField(blank=True, null=True)
    date_evaluated = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.score}"

class BaseUserManager(models.Manager):
    @classmethod

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    async def aget_by_natural_key(self, username):
        return await self.aget(**{self.model.USERNAME_FIELD: username})

