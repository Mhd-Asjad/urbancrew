from django.db import models
from products.models import *
from django.contrib.auth.models import User


# Create your models here.


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    added_date = models.DateField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    sizes = models.ForeignKey(ProductSize, on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField(null=True)
    total = models.IntegerField(null=True)
    def quantity1(self):
        prod_id = Product.objects.get(id=self.product_id)
        images = AddImages.objects.get(product_id=prod_id.id)
        stock = ProductSize.objects.get(image_id=images.id)
        return stock.stock
        
    def __str__(self):
        return f'{self.product.product_name}'
