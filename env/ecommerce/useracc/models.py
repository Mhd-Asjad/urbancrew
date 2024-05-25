from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Address(models.Model) :
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, default=None)
    last_name = models.CharField(max_length=100, default=None)
    email = models.EmailField(default="user@gmail.com")
    house = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    country = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=12)
    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class register(models.Model):

    Gender_Choice = [

        ("M" ,"Male"),
        ("F" , "Female"),
        ("O" , "Other")
    ]
    mobile = models.CharField(max_length=12, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True , null=True)
    dob = models.DateField(blank=True,null=True)
    gender = models.CharField(max_length=10, choices = Gender_Choice,blank=True)


@receiver(post_save,sender=User)
def create_Customer(sender,instance,created,**kwargs) :
    if created :
        register.objects.create(user = instance)
        print('customer createdd//!')
