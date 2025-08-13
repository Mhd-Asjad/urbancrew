from django.db import models
from adminapp.models import *
from products.models import * 

class Offer(models.Model) :
    CATEGORY  = 'category'
    PRODUCT = 'product'

    OFFER_TYPE_CHOICES = [

        ( CATEGORY, 'Category' ),
        ( PRODUCT, 'Product' ),

    ]
    offer_type = models.CharField(max_length=10,choices=OFFER_TYPE_CHOICES)
    categorys = models.ForeignKey(category,on_delete=models.CASCADE,null=True,blank=True)
    product = models.ForeignKey('products.Product',on_delete=models.CASCADE,null=True , blank=True)
    percentage = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)       
    end_date =  models.DateTimeField()

    def __str__(self):

        if self.offer_type == self.CATEGORY and self.categorys :
            return f'{self.categorys.name} - {self.percentage}% DISCOUNT TO {self.end_date}'
        elif  self.offer_type == self.PRODUCT and self.product :
            return f'{self.product.product_name} - {self.percentage}% DISCOUT TO {self.end_date}'
        else :
            return 'invalid offer'