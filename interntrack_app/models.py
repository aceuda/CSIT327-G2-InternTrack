

from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models

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
    ADMIN = 'admin', 'Admin'
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
        extra_fields.setdefault("role", UserRoles.ADMIN)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthdate = models.DateField(null=False)
    year_level = models.IntegerField(null=False)
    email = models.CharField(max_length=100)
    user_type = models.CharField(choices=UserRoles, default=UserRoles.STUDENT)
    username = models.CharField(unique=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    

class BaseUserManager(models.Manager):
    @classmethod

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    async def aget_by_natural_key(self, username):
        return await self.aget(**{self.model.USERNAME_FIELD: username})

