from django.db import models
from adminapp.models import category

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=200,unique=True)
    price = models.IntegerField()
    img = models.ImageField(upload_to='')
    is_available = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    categorys = models.ForeignKey(category,on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    def __str__(self) :
        return self.product_name

class AddImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.CharField(max_length=30)
    image1 = models.ImageField(upload_to='product_images/')
    image2 = models.ImageField(upload_to='product_images/')
    image3 = models.ImageField(upload_to='product_images/')
    
    def __str__(self):
        return f"{self.product.product_name} - {self.color}"

class ProductSize(models.Model):

    image = models.ForeignKey(AddImages, on_delete=models.CASCADE, related_name='sizes')

    size_choices = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),        
    ]

    size = models.CharField(max_length=10, choices=size_choices)
    stock = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.image.product.product_name} - {self.size}"