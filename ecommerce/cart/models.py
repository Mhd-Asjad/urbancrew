from django.db import models
from products.models import *
from django.contrib.auth.models import User
from adminapp.models import *
from  useracc.models import *
import razorpay
from django.conf import settings

# Create your models here.

class Cart(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    added_date = models.DateField(auto_now_add=True)
    product = models.ForeignKey(AddImages, on_delete=models.CASCADE, null=True)
    sizes = models.ForeignKey(ProductSize, on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField(null=True, blank=True)
    total = models.IntegerField(null=True)
    def quantity1(self):
        prod_id = Product.objects.get(id=self.product_id)
        images = AddImages.objects.get(product_id=prod_id.id)
        stock = ProductSize.objects.get(image_id=images.id)
        return stock.stock
    
    def total_amount(self) :
        if self.product and self.quantity:
            return self.product.product.price * self.quantity
        return 0

        
    def __str__(self):
        return f'{self.product.product.product_name}'
    

class Order(models.Model) :

    register = models.ForeignKey(register,on_delete=models.CASCADE)
    address = models.ForeignKey(Address,on_delete=models.DO_NOTHING,null=True,blank=True)
    payment_method = models.CharField(max_length=100,null=True)
    tracking_id = models.CharField(max_length=100,null=True)
    payment_transaction_id = models.CharField(max_length=100,null=True,blank=True)
    razorpay_order_id = models.CharField(max_length=100,null=True,blank=True)

    STATUS_CHOICES = (
        
        ("Delivered", "Delivered"),
        ("Pending", "Pending"),
        ("Payment Failed", "Payment Failed"),
        ("Payment Successful", "Payment Successful"),
        ("Returned", "Returned"),

    )

    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    sub_total = models.PositiveBigIntegerField(default=0,null=True,blank=True)
    shipping_charge = models.PositiveBigIntegerField(default=0, blank=True, null=True)
    total = models.IntegerField(default=0)
    paid = models.BooleanField(default=False)
    applied_coupen = models.ForeignKey(Coupon,on_delete=models.CASCADE,null=True)
    payment = models.OneToOneField('cart.Payment',on_delete=models.CASCADE,null = True)
    coupon_appliyed = models.BooleanField(null=True)
    discount_amount = models.IntegerField(default = 0)
    payment_success = models.BooleanField(default=False)

    def __str__(self):

        return f" order status : {self.status} payment method : {self.payment_method} paymentId {self.payment_transaction_id} "
    
    def create_razorpay_order(self) :
        order_amount = self.total * 100
        print(type(order_amount))
        order_currency = "INR"
        try :
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({

                'amount' : order_amount ,
                'currency' : order_currency,
                'payment_capture' : '1' 
            })
            self.razorpay_order_id = razorpay_order['id']
            self.save()

        except Exception as e :
            print(f'An erro occures {e}')
            raise

class Order_items(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_items')
    STATUS_CHOICES = (
        ("Order Placed", "Order Placed"),
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Out for Delivery" , "Out for Delivery"),
        ("Delivered", "Delivered"),
        ("Returned", "Returned"),
        ("Refunded", "Refunded"),
        ("Cancelled", "Cancelled"),

    )
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="pending")
    product = models.ForeignKey(AddImages,on_delete=models.CASCADE,related_name='order_products',
                                null=True,blank=True)
    price = models.PositiveBigIntegerField(default=0,null=True,blank=True)
    size = models.CharField(max_length=6,default='S')
    qnty = models.PositiveIntegerField(default=0)
    cancel_reason = models.TextField(blank=True,null=True)
    cancel = models.BooleanField(default=False)
    request_return = models.BooleanField(default=False)
    refund_processed = models.BooleanField(default=False)

    def __str__(self):
        return f" {self.product.product.product_name} {self.size} qnty : {self.qnty}  orders:{self.status}"
    

class Shipping_address(models.Model) :
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, default=None)
    last_name = models.CharField(max_length=100, default=None)
    email = models.EmailField(default="user@gmail.com")
    house = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=20)
    country = models.CharField(max_length=200)
    mobile_number = models.CharField(max_length=12)

    def __str__(self) :
        return f" Order Id :{self.order.tracking_id} {self.order.register.user} "

class Payment(models.Model):
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    transaction_id = models.CharField(max_length=100,null=True,blank=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True)
    pending = models.BooleanField(default=True)
    success = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)

    def __str__(self):
        status = ""

        if self.pending :
            status += "pending"
        
        if self.success :
            status += "success"

        if self.failed:
            status += "failed"

        return f' {status} payment' 

class Wishlist(models.Model) :
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(AddImages,on_delete=models.DO_NOTHING)
    size = models.ForeignKey(ProductSize,on_delete=models.CASCADE, null=True, blank=True)
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self) :
        return f'user : {self.user.username } product = {self.product.product.product_name}'