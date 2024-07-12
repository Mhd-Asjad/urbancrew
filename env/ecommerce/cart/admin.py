from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Cart)
admin.site.register(Order) 
admin.site.register(Order_items) 
admin.site.register(Payment)
admin.site.register(Shipping_address)
admin.site.register(Wishlist)