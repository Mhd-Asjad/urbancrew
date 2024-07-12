from django.db import models
from adminapp.models import *
from django.db.models.signals import post_save , post_delete , pre_save
from django.dispatch import receiver
from offer.models import *
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.postgres.fields import ArrayField


#productss models

class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    price = models.IntegerField()
    img = models.ImageField(upload_to="")
    is_available = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    categorys = models.ForeignKey(category, on_delete=models.CASCADE,related_name='cat')
    offer_price=models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name


class AddImages(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    color = models.CharField(max_length=30)
    image1 = models.ImageField(upload_to="product_images/")
    image2 = models.ImageField(upload_to="product_images/")
    image3 = models.ImageField(upload_to="product_images/")
    additional_images = ArrayField(models.ImageField(upload_to="product_images/"),blank=True,null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        
        return f"{self.product.product_name} - {self.color}"


class ProductSize(models.Model):

    product_id = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variants')
    image = models.ForeignKey(AddImages, on_delete=models.CASCADE, related_name="sizes")
    
    size = models.CharField(max_length=10,)
    stock = models.PositiveIntegerField(default=0)
    previous_stock = models.PositiveIntegerField(default=0,editable=False)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.image.product.product_name}  - {self.size} "

@receiver(post_save, sender=ProductSize)
@receiver(post_delete, sender=ProductSize)
def check_product_stock(sender, instance, **kwargs):
    product = instance.product_id
    image = instance.image
    
    all_sizes = ProductSize.objects.filter(product_id=product, image=image)
    total_stock = sum(size.stock for size in all_sizes)
    
    image.is_active = total_stock > 0
    image.save()
    
    all_images = AddImages.objects.filter(product=product)
    product.is_available = any(image.is_active for image in all_images)
    product.save()


@receiver([post_save,post_delete,pre_save],sender = Offer)
def update_offer_price(sender,instance,**kwargs) :
    product = instance.product
    category = instance.categorys
    today = timezone.now()
    print(today)


    if not instance.is_active and product :
        product.offer_price = 0

    if product and product.is_available == True :
        product_offers = Offer.objects.filter(product = product , is_active = True)
        Max_discound = 0

        for offer in product_offers :
            if offer.percentage > Max_discound :
                Max_discound =  offer.percentage

        full_amount = product.price
        if Max_discound > 0 :
            full_amount -= (full_amount * Max_discound / 100 )

        product.offer_price = round(full_amount)
        print(product.offer_price ,'ytuytyutyutyt')
        product.save()

    elif instance.is_active and category :
        
        products_in_category = Product.objects.filter(categorys = category)

        for product_in_category in products_in_category :

            product_offer_in_cat = Offer.objects.filter(product = product_in_category,is_active = True)
            print(product_in_category)
            print(product_in_category,'this is category offer for the products !!!')

            if product_offer_in_cat.exists() :

                biggest_discount = max(offer.percentage for offer in product_offer_in_cat)
            else :
                biggest_discount = 0

                print(biggest_discount ,'amount for the discount')

            category_offers = Offer.objects.filter(categorys=category)
            biggest_discount_in_category = max((offer.percentage for offer in category_offers ) , default=0)
            final_discount = max(biggest_discount,biggest_discount_in_category)
            final_price_in_cat  = product_in_category.price
            if final_discount > 0 :
                final_price_in_cat -= (final_price_in_cat * final_discount / 100)
            print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ' , final_price_in_cat)

            product_in_category.offer_price = round(final_price_in_cat)
            product_in_category.save()

def update_offer_price(self,**kwarg) :
    now = timezone.now()
    expired_offer = Offer.objects.get(end_date__lte = now , is_active = True)
    if expired_offer:   
        expired_offer.is_active = False
    expired_offer.save()

@receiver(pre_save, sender=Product)
def prod_offer_price(sender, instance, **kwargs):
    now = timezone.now()
    if instance.pk :
    # Check for an active product-specific offer

        product_offer = Offer.objects.filter(
            offer_type=Offer.PRODUCT,
            product=instance,
            is_active=True,
            end_date__gt=now
        ).first()

        if product_offer:
            discount = (product_offer.percentage / 100) * instance.price
            instance.offer_price = instance.price - discount
        else:
            # Check for an active category-specific offer
            category_offer = Offer.objects.filter(
                offer_type=Offer.CATEGORY ,
                categorys=instance.categorys,
                is_active=True,
                end_date__gt=now
            ).first()

            if category_offer:
                discount = (category_offer.percentage / 100) * instance.price
                instance.offer_price = instance.price - discount
            else:
                # No active offers, reset offer_price to the original price
                instance.offer_price = instance.price

# @receiver([post_save, post_delete], sender=Offer)
# def update_offer_price(sender, instance, **kwargs):
#     today = timezone.now()

#     if instance.product:
#         update_product_offer(instance.product)
#     elif instance.categorys:
#         update_category_offer(instance.categorys)

# def update_product_offer(product):
#     offers = Offer.objects.filter(product=product, is_active=True, end_date__gte=timezone.now())
#     if offers.exists():
#         max_discount = max(offer.percentage for offer in offers)
#         product.offer_price = product.price - (product.price * max_discount / 100)
#     else:
#         product.offer_price = None 
#     product.save()

# def update_category_offer(category):
#     products = Product.objects.filter(categorys=category)
#     for product in products:
#         update_product_offer(product)