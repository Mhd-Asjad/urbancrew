from django.db import models
from django.contrib.auth.models import User
from products.models import *

class category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_listed = models.BooleanField(default=True, null=True)
    is_deleted = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.name

class Coupon (models.Model) :
    coupon_code = models.CharField(max_length=100,unique=True)
    coupon_name = models.CharField(max_length=50)
    discount_percentage = models.IntegerField( default = 0 )
    minimum_amnt = models.PositiveBigIntegerField(blank=True,default = 0)
    max_amount = models.PositiveBigIntegerField(blank=True, default = 0 )
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True,blank=True)

    def __str__(self) :
        return f'{ self.coupon_name} min_amount : {self.minimum_amnt} to {self.max_amount}'