from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

class register(models.Model) :
    mobile = models.CharField(max_length=12,unique=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE,default=None)