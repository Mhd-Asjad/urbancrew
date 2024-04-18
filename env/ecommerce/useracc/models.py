from django.db import models
from django.contrib.auth.models import AbstractUser

class register(models.Model) :
    mobile = models.CharField(max_length=12,unique=True)