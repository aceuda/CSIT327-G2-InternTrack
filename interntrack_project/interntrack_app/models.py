from django.db import models

class UserRoles(models.TextChoices):
    """
    Create/Modify user roles here
    Add role in the same format (CUSTOM_ROLE = 'custom_role', 'Custom Role')
    """
    ADMIN = 'admin', 'Admin'
    STUDENT = 'student', 'Student'

class Intern(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    hours_completed = models.IntegerField(default=0)

    def __str__(self):
        return self.name
        
# Create your models here.
class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthdate = models.DateField(null=False)
    year_level = models.IntegerField(null=False)
    email = models.CharField(max_length=100)
    user_type = models.CharField(choices=UserRoles, default=UserRoles.ADMIN)



