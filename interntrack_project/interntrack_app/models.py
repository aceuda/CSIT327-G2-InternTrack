from django.db import models

class Intern(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    hours_completed = models.IntegerField(default=0)

    def __str__(self):
        return self.name
        
# Create your models here.
