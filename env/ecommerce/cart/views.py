from django.shortcuts import render, redirect, get_object_or_404
import razorpay.errors
from products.models import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse , HttpResponse , HttpResponseBadRequest
from useracc.models import *
import json
from django.db.models import Sum
import re
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string
import pdfkit
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from wallet.models import *
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
# Create your views here.

def add_cart(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            size_id = request.POST.get('size')
            product_id = request.POST.get('product_id')

            print(size_id)
            if  size_id is None:
                messages.error(request,"Select a size." )
                return redirect("shop_details", product_id)
            

            product = AddImages.objects.get(id=product_id)
            size = ProductSize.objects.get(id = size_id)
                    

            if size.stock <= 0 :

                messages.warning(request, "There is no stock left.")
                return redirect("shop_details", product_id)



            print(product_id,'this is prod id')
            print(size_id,'sizess')


            if Cart.objects.filter(user = request.user ,product = product ,sizes = size).exists():
                messages.warning(request,'this item already in the cart')
                return redirect("shop_details", product_id)

            else :
                
                clear_coupon_session(request)

                wishlist = Wishlist.objects.filter(user = request.user,product = product_id)
                if wishlist.exists() : 
                    wishlist.delete()
                Cart.objects.create(user=request.user, product=product , sizes = size , total=product.product.price , quantity=1)
                messages.success(request, 'Item added to cart successfully.')
                return redirect("shop_details", product_id)
            
        messages.error(request, "This product cannot add to cart.")
        return redirect('cart')
    else :
        messages.error(request,'cant add without login')
        return redirect('user_login')
            
def remove_cart(request, cart_id) :
    cart_item = Cart.objects.get(id=cart_id, user=request.user)
    cart_item.delete()

    return redirect("cart")

from decimal import Decimal

@login_required(login_url="user_login")
def cart_view(request):
    user = request.user.id
    cart_items = Cart.objects.filter(user=user)
    subtotal_agg = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
    subs_amnt = subtotal_agg["sum"] or Decimal(0) 
    shippingfee = Decimal(0.00)

    subtotal = Decimal(0)
    for item in cart_items:
        if item.product.product.offer_price:
            item.total = item.product.product.offer_price * item.quantity
        else:
            item.total = item.product.product.price * item.quantity
        subtotal += item.total
        item.save()

    if not cart_items.exists() :
        shippingfee = 0

    elif subtotal < 5000 or subs_amnt > 0 :
        shippingfee = Decimal(100)

    else:
        shippingfee = 0

    full_total = subtotal + shippingfee

    context = {

        "subtotal": subtotal,
        "full_total": full_total,
        "cart_items": cart_items,
        "shippingfee": shippingfee,
    }

    return render(request, "cart.html", context)

@csrf_exempt
def update_tot_price(request):
    data = json.loads(request.body)
    cartid = data.get("cartid")
    user = request.user
    if request.method == "POST":
        data = json.loads(request.body)
        if data.get("operation") == "increment":
            quantity = data.get("quantity")
            cartid = data.get("cartid")
            cart_items = Cart.objects.get(id=cartid,user=user)
            stocks = ProductSize.objects.get( id= cart_items.sizes.id)
            if quantity < stocks.stock :
                cart_items.quantity += 1
                clear_coupon_session(request)
                if cart_items.product.product.offer_price :
                    cart_items.total = cart_items.product.product.offer_price * cart_items.quantity
                else :
                    cart_items.total = cart_items.product.product.price * cart_items.quantity
                cart_items.save()
                subtotal = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
                subs_amnt = subtotal["sum"]
                shippingfee = 100
                if subs_amnt < 5000 :
                    full_total = subs_amnt + shippingfee
                else:
                    full_total = subs_amnt
                return JsonResponse(
                    {
                        "success": True,
                        "message": "updated",
                        "total": cart_items.total,
                        "subtotal": subtotal["sum"],
                        "full_total" : full_total ,

                    },
                )
            else:
                clear_coupon_session(request)
                return JsonResponse({"success": False, "message": "notupdated"})
        elif data.get("operation") == "decrease" :
            quantity = data.get("quantity")
            cartid = data.get("cartid")
            cart_items = Cart.objects.get(id=cartid,user=user)
            # product = cart_items.product.id
            stocks = ProductSize.objects.get( id= cart_items.sizes.id)
            cart_items.quantity -= 1
            clear_coupon_session(request)
            if cart_items.product.product.offer_price :
                cart_items.total = cart_items.product.product.offer_price * cart_items.quantity
            else :
                cart_items.total = cart_items.product.product.price * cart_items.quantity
            cart_items.save()
            subtotal = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
            subs_amnt = subtotal["sum"]
            print(subs_amnt)
            shippingfee = 100
            if subs_amnt < 5000:
                full_total = subs_amnt + shippingfee
            else:
                full_total = subs_amnt
            print(full_total)

            return JsonResponse(
                {
                    "success": True,
                    "message": "dec_updated" ,
                    "total": cart_items.total ,
                    "subtotal": subtotal["sum"],
                    "full_total": full_total,
                    "shippingfee" : shippingfee
                },
            )

def wishlist_view(request) :
    user = request.user
    wishlist_items = Wishlist.objects.filter(user=user.id)

    context = {

        'wishlist_items' : wishlist_items,
        # 'product' : product
    }
    return render(request,'wishlist.html',context)

def add_to_wishlist(request,product_id) :   
    if request.user.is_authenticated :
        product = AddImages.objects.get(id=product_id)
        if Wishlist.objects.filter(user = request.user ,product=product).exists():
            messages.error(request,'this product already exist in wishlist')
            return redirect('shop_details',product_id)

        wish_items = Wishlist.objects.create(
            user = request.user,
            product = product,

        )

        if wish_items :
            messages.success(request,'item added to wishlist succesfully ')
        else :

            messages.error(request,'this is already in the cartttttt.....!')
        
        return redirect('wishlistview')
    return redirect('user_login')


def remove_item_wishlist(request,wihslist_id) :
    user = request.user
    wish_prod = Wishlist.objects.get(id = wihslist_id,user=user)
    wish_prod.delete()
    messages.success(request,'removed from your wishlist')
    return redirect('wishlistview')

def additional_address(req):

    if req.method == 'POST' :
        
        print('this is takingggg')
        
        user = User.objects.get(id=req.user.id)
        print(user.id,'addressssssssssssssssssss')
        first_name = req.POST.get('first_name')
        last_name = req.POST.get('last_name')
        email = req.POST.get('email')
        house = req.POST.get('house')
        city = req.POST.get('city')
        state = req.POST.get('state')
        country = req.POST.get('country')
        pin_code = req.POST.get('pin_code')
        phone = req.POST.get('mobile_number')

        
        error_message = {}

        if not all([ first_name,last_name,email,house,city,state,country,pin_code,phone]) :
            messages.error(req,'all fields is required')
            return redirect('new_address')
        
        name_pattern = r'^[a-zA-Z]+(?:\s[a-zA-Z]+)*$'
        if not re.match(name_pattern, first_name):
            error_message['first_name'] = 'First name can only contain letters and single spaces.'
        if not re.match(name_pattern, last_name):
            error_message['last_name'] = 'Last name can only contain letters and single spaces.'

        try:
            validate_email(email)
        except ValidationError:
            error_message['email'] = 'Enter a valid email address.'

        phone_pattern = r'^\d{11}$'
        if not re.match(phone_pattern, phone):
            error_message['phone'] = 'Enter a valid 10-digit mobile number.'

        pin_code_pattern = r'^\d{5,6}$'
        if not re.match(pin_code_pattern, pin_code):
            error_message['pin_code'] = 'Enter a valid 5 or 6-digit pin code.'

        if error_message:
            for key, message in error_message.items():
                messages.error(req, message)
            return redirect('new_address')
                    
        # if Address.objects.filter(user = user , first_name__iexact=first_name, last_name__iexact=last_name , house__iexact=house, city__iexact=city, state__iexact=state, country__iexact=country, pin_code__iexact=pin_code, mobile_number__iexact=phone).exists():
        #     messages.error(req, 'This address already exists. Cannot add duplicate address.')
        #     return redirect('new_address')
        
        address = Address.objects.create(

            user=user,
            first_name = first_name,
            last_name = last_name,
            email = email,
            house = house,
            city = city , 
            state = state , 
            country = country , 
            pin_code = pin_code,
            mobile_number = phone

        )
        
        messages.success(req, 'address addedd succesfully')
        print('address added')
        return redirect('checkout')
    
    states = [

        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
        'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
        'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'

    ]

    
    return render(req,'add_address.html' , {'states' : states})


def add_coupon_to_session(request ,coupon_id) :
    coupon = Coupon.objects.get(id = coupon_id)
    request.session['coupon_applied'] = coupon.is_active
    request.session['coupon_id'] = coupon.id
    request.session['coupon_code'] = coupon.coupon_code
    request.session['coupon_name'] = coupon.coupon_name
    request.session['discount_percentage'] = coupon.discount_percentage
    return redirect(request,'checkout.html')


def clear_coupon_session(request):
    if request.session.get('coupon_applied'):
        del request.session['coupon_applied']
        del request.session['coupon_id']

def apply_coupon(req):
    if not req.user.is_authenticated:
        messages.error(req, 'You need to log in to apply a coupon.')
        return redirect('login')

    today = timezone.now()

    if req.method == 'POST':
        userid = req.user.id
        coupon_code = req.POST.get('coupon_code')
        action = req.POST.get('action')

        if action == 'remove_coupon':
            if req.session.get('coupon_applied', True):
                req.session['coupon_applied'] = False
                messages.success(req, 'Coupon has been removed.')
            else:
                messages.error(req, 'No coupon has been applied.')
            return redirect('checkout')

        if coupon_code:
            if req.session.get('coupon_applied', False):
                messages.error(req, 'A coupon has already been applied...!')
                return redirect('checkout')

            coupon = Coupon.objects.filter(
                coupon_code=coupon_code,
                expiry_date__gt=today,
                is_active=True
            ).first()


            if not coupon:
                messages.error(req, 'invalid coupon code or may be expired')
                return redirect('checkout')

            if Order.objects.filter(register__user__id =userid, applied_coupen__coupon_code=coupon_code).exists():
                messages.error(req, 'You have already used this coupon. ')
                return redirect('checkout')
            
            cart_items = Cart.objects.filter(user=req.user)
            sub_total = cart_items.aggregate(total=Sum('total'))['total'] or 0
            
            shipping_fee = 0 

            if sub_total < 5000 :
                shipping_fee = 100 
            else : 
                shipping_fee = 0

            total = sub_total + shipping_fee
            print('total amount in checkout',total)


            if total <= coupon.minimum_amnt or total >= coupon.max_amount :
                messages.error(req, f'Your total amount must be between ₹{coupon.minimum_amnt} and ₹{coupon.max_amount} to apply this coupon.')
                return redirect('checkout')

            req.session['coupon_id'] = coupon.id
            req.session['coupon_name'] = coupon.coupon_name
            req.session['coupon_applied'] = True

            messages.success(req, 'Coupon applied successfully.')

            return redirect('checkout')

    return render(req,'checkout.html',{'coupon_applied' : req.session.get('is_applied') })

from django.db.models import Q

@never_cache
def checkout(req):
    today = timezone.now()
    if req.user.is_authenticated:
        user = req.user
        customer = User.objects.get(username=req.user.username)
        cart_items = Cart.objects.filter(user=customer)

        if not cart_items.exists():
            messages.error(req, "The Cart is empty.")
            return redirect('cart')

        try:
            Addresses = Address.objects.filter(user=user, is_deleted=False)
        except Address.DoesNotExist:
            Addresses = None

        subtotal = cart_items.aggregate(sum=Sum('total'))['sum'] or 0
        shipping_fee = 0 if subtotal > 5000 else 100
        full_total = subtotal + shipping_fee
        discount_amount = 0
        coupon_code = None

        wallet = Wallet.objects.get(user = user)

        for cart_item in cart_items:
            product_size = cart_item.sizes
            prod = cart_item.product
            errors = []

            if not prod.product.is_available or not prod.is_active or prod.product.is_deleted :
                errors.append(f"Product {prod.product.product_name} - {product_size.size} or its variant is no longer available.")
                cart_item.delete()

            if cart_item.quantity > product_size.stock:
                errors.append(f"Insufficient stock for {prod.product.product_name}, only {product_size.stock} left.")

        if errors:
            for error in errors:
                messages.error(req, error)
            return redirect('cart')

        available_coupon = Coupon.objects.filter(
            Q(minimum_amnt__lte=full_total) & Q(max_amount__gte=full_total) & Q(is_active=True) & Q(expiry_date__gte = today)
        )[:2]
        
        if req.session.get('coupon_applied', False) :
            coupon_id = req.session.get('coupon_id')
            coupon = Coupon.objects.filter(id=coupon_id).first()
            
            if coupon is not None:
                discount_amount = (subtotal * coupon.discount_percentage) / 100
                subtotal -= round(discount_amount)
                full_total -= round(discount_amount)
                coupon_code = coupon.coupon_code

        context = {

            'cart_items': cart_items,
            'addresses': Addresses,
            'sub_total': subtotal,
            'shipping_fee': shipping_fee,
            'full_total': full_total,
            'coupon_applied': req.session.get('is_applied', True),
            'discount_amount': discount_amount,
            'coupon_code': coupon_code,
            'available_coupons': available_coupon,
            'wallet': wallet,

        }

        return render(req, 'checkout.html', context)
    
    else :
        messages.error(req, 'You need to be logged in to checkout.')
        return redirect('user_login')
    
@never_cache
def place_order(request) :
    customer = User.objects.get(username = request.user.username)
    cart_items = Cart.objects.filter(user=customer)
    register_user = register.objects.filter(user=customer).first()
    if request.method == 'POST' :
        address_id = request.POST.get('select_address')

        if address_id is None :

            messages.error(request,'please select a address')
            return redirect('checkout')
        
        try :

            address = Address.objects.get(id = address_id)

        except Address.DoesNotExist :

            messages.error(request,'No address mentioned. Please add an address.')
            return redirect('checkout')

        pm = request.POST.get('payment_method') 

        if pm is None :
            messages.error(request,'payment method is unavailable')
            return redirect('checkout')
        
        if pm == 'COD' :
        
            customer = User.objects.get(username = request.user.username)
            cart_items = Cart.objects.filter(user = customer)

            register_user = register.objects.get(user=customer.id)
            sub_total = sum(item.total for item in cart_items)


            if sub_total < 5000 :
                shipping_fee = 100
            else :
                shipping_fee = 0

            full_total = sub_total if sub_total >= 5000 else sub_total + shipping_fee

            order_id = get_random_string(8,'abcdfgh123456789')
            while Order.objects.filter(tracking_id = order_id).exists():
                order_id = get_random_string(8,'abcdfgh123456789')

            discount_amount = 0
            if request.session.get('coupon_applied'):
                coupon_id = request.session.get('coupon_id')
                applied_coupon = Coupon.objects.get(id = coupon_id)
                discount_amount = ( sub_total * applied_coupon.discount_percentage ) / 100
                sub_total -= discount_amount

            else:

                applied_coupon = None

            if full_total > 1000 :
                messages.error(request,'cash on delivery only available under 1000rs purchase ')
                return redirect('checkout')

            order = Order.objects.create (
                register = register_user ,
                address = address ,
                payment_method = pm ,
                status = 'Order placed',
                sub_total = sub_total ,
                shipping_charge = shipping_fee , 
                total = full_total ,
                paid = False ,
                tracking_id = order_id,
                applied_coupen = applied_coupon  ,
                coupon_appliyed = request.session.get('coupon_applied'),
                discount_amount = discount_amount 
            )
            print('rerggg' , register_user),
            print('address')


            shipping_address = Shipping_address.objects.create(

                order = order, 
                first_name = address.first_name,
                last_name = address.last_name,
                email = address.email ,
                house = address.house , 
                city = address.city ,
                state = address.state,
                pin_code = address.pin_code,
                country = address.country,
                mobile_number = address.mobile_number

            )
            
            for item in cart_items :
                product_size = item.sizes 
                if product_size.stock >= item.quantity :
                    product_size.stock -= item.quantity
                    product_size.save()

                
            for item in cart_items :
                items = Order_items.objects.create(

                    order = order , 
                    status = "Order Placed" ,
                    product = item.product,
                    price = item.product.product.price,
                    qnty = item.quantity,
                    size = item.sizes.size

                )

                if request.session.get('coupon_applied') == True :
                    del request.session['coupon_applied']
                    del request.session['coupon_id']

            for item in cart_items:
                product_size = item.sizes
                product_size.stock -= item.quantity
                product_size.save()

            cart_items.delete()
            return redirect('order_success')
            
        elif pm == "razorpay" :

            customer = User.objects.get(username = request.user.username)
            cart_items = Cart.objects.filter(user=customer)
            register_user = register.objects.filter(user=customer.id).first()
            print(register_user,'uesrsss')
            print(register_user)
            sub_total = sum(item.total for item in cart_items)
            shipping_fee = 0
            print('this is the sub_total :',sub_total)

            address_obj = get_object_or_404(Address,id = address_id)

            if sub_total < 5000 :
                shipping_fee = 100
            else :
                shipping_fee = 0

            full_total = sub_total if sub_total >= 5000 else sub_total + shipping_fee
            print('full_amount',full_total)

            order_id = get_random_string(8,'abcdfgh123456789')
            while Order.objects.filter(tracking_id = order_id).exists():
                order_id = get_random_string(8,'abcdfgh123456789')

            discount_amount = 0

            print(sub_total)
            if request.session.get('coupon_applied'):
                coupon_id = request.session.get('coupon_id')
                applied_coupon = Coupon.objects.get(id = coupon_id)
                discount_amount = ( sub_total * applied_coupon.discount_percentage ) / 100
                print(discount_amount,'disc')
                full_total -= discount_amount
            else:
                applied_coupon = None

                print('this is the discount amounntttt : ',discount_amount)
                print('applied ccoupoonnnn' , applied_coupon)
            order_id = get_random_string(8,'abcdfgh123456789')
            while Order.objects.filter(tracking_id = order_id).exists():
                order_id = get_random_string(8,'abcdfgh123456789')

            print(register_user.id)
            request.session['register'] = register_user.id
            request.session['address_id'] = address_id
            request.session['total'] = full_total
            request.session['discount_amount'] = discount_amount
            request.session['applied_coupon'] = coupon_id if applied_coupon else None


            temp_order = Order.objects.create(

                register = register_user ,
                address = address_obj ,
                payment_method = pm,
                tracking_id = order_id ,
                shipping_charge = shipping_fee,
                total = int(full_total),
                paid = False ,
                applied_coupen = applied_coupon,
                coupon_appliyed = request.session.get('coupon_applied'),
                discount_amount = int(discount_amount) ,
                status = 'Pending'

            )

            temp_order.create_razorpay_order()

            shipping_address = Shipping_address.objects.create(

                order = temp_order, 
                first_name = address.first_name,
                last_name = address.last_name,
                email = address.email ,
                house = address.house , 
                city = address.city ,
                state = address.state,
                pin_code = address.pin_code,
                country = address.country,
                mobile_number = address.mobile_number
            )
            
            print('temp order createdd')
            request.session['order_id'] = temp_order.id
            return redirect('razorpay_order_summary')
        
        elif pm == 'wallet' :

            user_customer = customer
            print(user_customer)
            balance = Wallet.objects.get(user = user_customer)

            sub_total = sum(item.total for item in cart_items)

            shipping_fee = 0

            if sub_total < 5000 :
                shipping_fee = 100

            else :

                shipping_fee = 0

            full_total = sub_total if sub_total > 5000 else sub_total + shipping_fee

            if balance.balance < full_total :
                messages.error(request,'insufficient blance in your wallet')
                return redirect('checkout')


            
            transaction_id = "WW_" + get_random_string(4, "ABC123456789")
            while Order.objects.filter(tracking_id=transaction_id).exists():
                transaction_id = "WW_" + get_random_string(
                    4, "ABC123456789"
                )
            
            order_id = get_random_string(8,'abcdfgh123456789')
            while Order.objects.filter(tracking_id = order_id).exists():
                order_id = get_random_string(8,'abcdfgh123456789')
            discount_amount= 0
            if request.session.get('coupon_applied'):
                coupon_id = request.session.get('coupon_id')
                applied_coupon = Coupon.objects.get(id = coupon_id )
                discount_amount = ( sub_total * applied_coupon.discount_percentage ) / 100
                print(discount_amount,'disc')
                full_total -= discount_amount
            else:
                applied_coupon = None
            
            request.session['discount'] = discount_amount

            order = Order.objects.create(
                register = register_user,
                address= address ,
                payment_method = 'Wallet',
                tracking_id = order_id,
                status = 'Payment Successful',
                sub_total = sub_total ,
                total = full_total,
                paid = True ,
                coupon_appliyed = request.session.get('coupon_applied'),
                applied_coupen = applied_coupon,
                discount_amount = request.session.get('discount')

            )
            shipping_address = Shipping_address.objects.create(

                order = order, 
                first_name = address.first_name,
                last_name = address.last_name,
                email = address.email ,
                house = address.house , 
                city = address.city ,
                state = address.state,
                pin_code = address.pin_code,
                country = address.country,
                mobile_number = address.mobile_number

            )
            
            paymnet = Payment.objects.create(
                amount = full_total,
                transaction_id = transaction_id ,
                paid_at = timezone.now(),
                pending=False,
                success=True

            )

            for item in cart_items:
                product_size = item.sizes
                product_size.stock -= item.quantity
                product_size.save()


            for item in cart_items :
                od = item.sizes

                order_items = Order_items.objects.create(
                    order = order,
                    product = item.product ,
                    price = item.product.product.offer_price,
                    size = item.sizes.size ,
                    qnty = item.quantity , 
                    status = 'Order placed'
                )
        
            balance.balance -= full_total
            balance.save()

            wallet = Wallet_transactions.objects.create(
                wallet = balance ,
                type = 'withdrawal',
                amount = full_total ,
                transaction_id = transaction_id ,
                description = 'money withdrwed',
                time_stamp = timezone.now()

            )
            cart_items.delete()
            return redirect('order_success')
    return redirect('checkout')
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

login_required(login_url='user_login')
@never_cache
def razorpay_view(request):
    cart = Cart.objects.filter(user = request.user).exists()
    if request.user.is_authenticated :

        payment_id = request.session.get('payment_id')
        if cart :
            total = request.session.get('total')
            print('totall razz:',total)
            razorpay_order_id = ''
            order_currency = "INR"

            razorpay_order = client.order.create(dict(amount=int(total * 100), currency=order_currency, payment_capture=1))
            razorpay_order_id = razorpay_order['id']

            context = {

                'amount' : total ,
                'currency' : order_currency ,
                'order_id' : razorpay_order_id ,

            }
            payment = Payment.objects.create(amount = total , transaction_id = razorpay_order_id , pending = True )
            request.session['payment_id'] = payment.id

            return render(request, 'razorpay_summary.html', context)
        else:
            messages.success(request,'you transaction stored succesfully')
            return redirect('user_profile')
    return render(request, 'razorpay_summary.html')

@never_cache
@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.session.get('payment_id')
        payment = get_object_or_404(Payment, id = payment_id)    
        total = request.session.get('total')
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        print('razorpay payment', razorpay_payment_id)
        razorpay_signature = request.POST.get("razorpay_signature")
        print(razorpay_signature)
        payment_error = request.POST.get("payment_error", "")

        params_dict = {

            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:

            client.utility.verify_payment_signature(params_dict)
            payment_status = True
            
        except razorpay.errors.SignatureVerificationError :
            payment_status = False

            print(payment_status,'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        with transaction.atomic():
            if payment.paid :
                return redirect('user_profile')
            else :
                payment.paid = payment_status
                print(payment_status)
                payment.pending = not payment_status
                print(not payment_status)
                payment.success = payment_status
                payment.failed = True if not payment_status else False
                payment.paid_at = timezone.now() if payment_status else None
                payment.save()

            order_id = request.session.get('order_id')
            order = get_object_or_404(Order, id = order_id)

            if payment_status :
                order.payment_success = True
                order.paid = True
                order.status = 'Payment Successful'
            else:
                order.payment_success = False
                order.paid = False
                order.status = 'Pending'

            order.payment = payment
            print(payment_status,'helloooowww1')
            order.save()

            cart_items = Cart.objects.filter(user=request.user)

            for item in cart_items :
                product_size = item.sizes
                if product_size.stock >= item.quantity :
                    product_size.stock -= item.quantity
                    product_size.save()
                print(item.product,'productsssssssssssssssssssssssssssss')
                Order_items.objects.create(
                    order=order,
                    status= 'Order Placed' if payment_status else 'Payment Failed',
                    product=item.product ,
                    price =  item.product.product.offer_price ,
                    qnty=item.quantity,
                    size=item.sizes.size
                )

            if payment_status :
                cart_items.delete()
                clear_coupon_session(request)

            else :
                cart_items.delete()
                clear_coupon_session(request)
                return render(request,'order_failure.html',{'error_messages':payment_error})
    return render(request, 'order_success.html')


login_required(login_url='user_login')
@never_cache
def payment_confirmation(request):
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        razorpay_order_id = request.POST.get('order_id')
        
        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id, register__user=request.user)
            if order:
                order.payment_transaction_id = payment_id
                order.status = "Payment Successful"
                order.paid = True
                order.save()

                order_items = Order_items.objects.filter(order=order)
                order_items.update(status="Order Placed")

                # for i in order_items :
                #     product_qnty = ProductSize.objects.get(product = i.product , size = i.size)
                #     product_qnty.stock -= i.qnty
                #     product_qnty.save()

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Order not found.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def order_failure(request) :
    return render(request,'order_failure.html')

@login_required(login_url='user_login')
def order_details(request, order_id) :
    try :
        print(order_id,'this is theh order iddd')
        order = Order.objects.get(id = order_id ,register__user = request.user)
        order_items = Order_items.objects.filter(order=order).order_by('-id')
        user_address = Address.objects.filter(user = request.user , is_deleted = False)
        shipping_address = Shipping_address.objects.get(order = order)
        status = order.status
        print(status,'@@@@@@@@@@@@@@@@@@@@@@@@@@')
        print(shipping_address)
        print(order_items,'orderedd')
        amount_in_paisa = order.total * 100
        
        context = {

            'order' : order ,
            'order_items' : order_items,
            'shipping' : shipping_address,
            'user_addresses' : user_address,
            'amount_in_paisa' : amount_in_paisa,
            'status' : status

        }
        return render(request,'order_details.html',context)
    
    except Order.DoesNotExist:
        return render(request, 'error.html', {'message': 'Order not found.'})
    
    except Shipping_address.DoesNotExist :
        return render(request, 'error.html', {'message': 'Shipping address not found.'})
    
def change_shipping_address(request,order_id):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
            order = Order.objects.get(id=order_id, register__user=request.user)
            shipping_address = Shipping_address.objects.get(order=order)
            shipping_address.first_name = address.first_name
            shipping_address.last_name = address.last_name
            shipping_address.email = address.email
            shipping_address.house = address.house
            shipping_address.city = address.city
            shipping_address.state = address.state
            shipping_address.pin_code = address.pin_code
            shipping_address.country = address.country
            shipping_address.mobile_number = address.mobile_number
            shipping_address.save()
            messages.success(request, 'Shipping address updated successfully.')
            return redirect('order_details',order_id)
        except Address.DoesNotExist:
            messages.error(request, 'Address does not exist.')
        except Shipping_address.DoesNotExist:
            messages.error(request, 'Shipping address for this order does not exist.')

    return redirect('order_details', order_id=order_id)


def cancel_order_item(req, item_id):
    order_item = Order_items.objects.get(id=item_id)
    if order_item.order.register.user == req.user :
        if req.method == 'POST' :
            
            cancel_reasons = req.POST.get('cancel_reason')
            order_item.cancel = True
            order_item.status = "Cancelled"
            order_item.cancel_reason = cancel_reasons
            order_item.save()

            messages.success(req ,'order item cancelled')
            return redirect('order_details',order_item.order.id)
        
        if order_item.order.payment_method in ['razorpay', 'Wallet']:
            print('in iaammsadm')
            cancel_refund(req,item_id)
            
    return render(req,'cancel.html', {'order_item': order_item })


@login_required
def cancel_refund(request, cancel_id):
    try:
        cancel_item = get_object_or_404(Order_items, id=cancel_id)
    except Order_items.DoesNotExist:
        messages.error(request, 'Invalid order item for cancellation.')
        return redirect('ordered_item')

    order = cancel_item.order

    if order.payment_method in ['razorpay', 'Wallet'] and not cancel_item.refund_processed:
        coupon_amount = order.discount_amount if order.applied_coupen else 0
        total_quantity = Order_items.objects.filter(order=order).aggregate(total_quantity=Sum('qnty'))['total_quantity'] or 1
        discount_for_item = Decimal(coupon_amount) / Decimal(total_quantity)

        offer_price = cancel_item.product.product.offer_price or cancel_item.product.product.price
        item_total = (Decimal(offer_price) - discount_for_item) * Decimal(cancel_item.qnty)

        non_returned_items_count = Order_items.objects.filter(order=order).exclude(status__in=['Cancelled', 'Refunded']).count()
        
        if non_returned_items_count > 1:
            refund_amount = item_total
        else:
            refund_amount = item_total
            if order.applied_coupen:
                coupon = Coupon.objects.get(coupon_code=order.applied_coupen.coupon_code)
                if order.total < coupon.minimum_amnt:
                    order.applied_coupen = None
                    refund_amount = item_total - order.discount_amount
                    order.total += order.discount_amount
                else:
                    refund_amount = order.total

        order.total -= refund_amount
        order.save()

        for size in ProductSize.objects.filter(size=cancel_item.size, image=cancel_item.product):
            size.stock += cancel_item.qnty
            size.save()

        user = order.register.user
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance += refund_amount
        wallet.save()

        transaction_id = "Ca_" + get_random_string(6, 'ABCPMOZ456789')
        while Wallet_transactions.objects.filter(transaction_id=transaction_id).exists():
            transaction_id = "Ca_" + get_random_string(6, 'ABCPMOZ456789')

        Wallet_transactions.objects.create(
            wallet=wallet,
            type='Refund',
            amount=refund_amount,
            description='Cancel refund',
            transaction_id=transaction_id,
            time_stamp=timezone.now()
        )

        cancel_item.refund_processed = True
        cancel_item.status = 'Cancelled'
        cancel_item.save()

        messages.success(request, f'Amount of ₹{refund_amount} has been added to {user.username}\'s wallet.')
        return redirect('order_details', order_id=order.id)

    messages.error(request, "Already tried for cancellation refund or not eligible.")
    return redirect('order_details', order_id=order.id)


def request_return_order_item(req , item_id) :

    try:
        order_items = Order_items.objects.get(id=item_id)
        print(order_items,'fhksdhkshah')
    except Order_items.DoesNotExist:
        pass

    if req.user.is_authenticated:
        if order_items.order.register.user == req.user and order_items.status == 'Delivered' :
            if not order_items.request_return :
                order_items.request_return = True
                order_items.save()
                messages.success(req,'return request has been submitted')
                return redirect('order_details', order_id = order_items.order.id)

        else :
            
            messages.error(req,'you can only return products after delivery of product')
            if order_items :
                return redirect('order_details', order_id = order_items.order.id)
        
    context = {

        'order_items': order_items

    }
        
    return render(req ,'order_details.html',context)

def invoice(request, order_id) :

    if request.user.is_authenticated :
        customer = register.objects.filter(user = request.user).first()
        print(customer)
        try :
            order_items = Order_items.objects.filter(order__id = order_id , order__register = customer)
            print(order_items)
        except register.DoesNotExist :
            messages.error(request,'this product havet reachedd.....!')

        order = Order.objects.get(id=order_id, register=customer)
        
        total = Decimal(0)
        for i , item in enumerate(order_items,1):
            product = item.product.product
            price = item.price
            print(i ,':', price)
            print(' og price : ',product.price, 'off price :',product.offer_price)
            total += Decimal(price) * item.qnty

        shipping_fee = order.shipping_charge

        if order.applied_coupen :
            coupon_code = order.applied_coupen.coupon_code
            discount = total * (order.applied_coupen.discount_percentage ) / Decimal(100)
            total += 100 if shipping_fee else 0
            total -= discount

        else :
            coupon_code = 'no applied coupon'
            discount = Decimal(0)
            total +=   100 if shipping_fee else 0


        context = {
            'order_items' : order_items,
            'customer' : customer,
            'total' : total,
            'shipping_charge' : shipping_fee,
            'coupon': {
                'code': coupon_code,
                'discount': discount,
            }
        }

        html_string = render_to_string("invoice.html",context)
        config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')


        # generating pdf

        pdf = pdfkit.from_string(html_string, False,configuration=config)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="invoice.pdf"'
        return response
    
    else :

        return redirect('user_login')


# def is_offer_active(product_id):

#     now = timezone.now()
    
#     # Query for any active offers for the product that haven't expired yet
#     active_offers = Offer.objects.filter(
#         product_id=product_id ,
#         is_active=True,
#         end_date__gt=now  # Ensure the offer hasn't ended
#     ).exists()

#     return active_offers
