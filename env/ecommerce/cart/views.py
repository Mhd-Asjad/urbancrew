from django.shortcuts import render, redirect, get_object_or_404
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
from django.contrib.sites.shortcuts import get_current_site





# Create your views here.

def add_cart(request):

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

            messages.error(request, "There is no stock left.")
            return redirect('shop_details', product_id)

        print(product_id,'this is prod id')
        print(size_id,'sizess')

        if Cart.objects.filter(user = request.user ,product = product ,sizes = size).exists():
            messages.error(request,'this item already in the cart')
            return redirect("shop_details", product_id)

        else :
            # clear_coupon_session(request)

            Cart.objects.create(user=request.user, product=product , sizes = size , total=product.product.price , quantity=1)
            messages.success(request, 'Item added to cart successfully.')
            return redirect("shop_details", product_id)
           
    messages.error(request, "This product cannot add to cart.")
    return redirect('cart')
            
def remove_cart(request, cart_id) :
    cart_item = Cart.objects.get(id=cart_id, user=request.user)
    cart_item.delete()
    # clear_coupon_session(request)

    return redirect("cart")

from decimal import Decimal

@login_required(login_url="user_login")
def cart_view(request):
    user = request.user.id
    cart_items = Cart.objects.filter(user=user)
    subtotal_agg = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
    subs_amnt = subtotal_agg["sum"] or Decimal(0)  # Handle case when sum is None
    shippingfee = Decimal(0)
    
    subtotal = Decimal(0)
    for item in cart_items:
        if item.product.product.offer_price:
            item.total = item.product.product.offer_price * item.quantity
        else:
            item.total = item.product.product.price * item.quantity
        subtotal += item.total
        item.save()

    if subtotal < 5000:
        shippingfee = Decimal(100)

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
                if cart_items.product.product.offer_price :
                    cart_items.total = cart_items.product.product.offer_price * cart_items.quantity
                else :
                    cart_items.total = cart_items.product.product.price * cart_items.quantity
                cart_items.save()
                subtotal = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
                subs_amnt = subtotal["sum"]
                print("this is sub", subtotal)
                print( subs_amnt )
                shippingfee = 100
                if subs_amnt < 5000:
                    full_total = subs_amnt + shippingfee
                else:
                    full_total = subs_amnt
                return JsonResponse(
                    {
                        "success": True,
                        "message": "updated",
                        "total": cart_items.total,
                        "subtotal": subtotal["sum"],
                        "full_total": full_total,
                    },
                )
            else:
                # clear_coupon_session(request)
                return JsonResponse({"success": False, "message": "notupdated"})
        elif data.get("operation") == "decrease":
            quantity = data.get("quantity")
            cartid = data.get("cartid")
            cart_items = Cart.objects.get(id=cartid,user=user)
            # product = cart_items.product.id
            stocks = ProductSize.objects.get( id= cart_items.sizes.id)
            cart_items.quantity -= 1
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
                    "message": "dec_updated",
                    "total": cart_items.total,
                    "subtotal": subtotal["sum"],
                    "full_total": full_total,
                    "shippingfee" : shippingfee

                },
            )
        
def wishlist_view(request) :
    user = request.user
    wishlist = Wishlist.objects.filter(user=user)

    context = {

        'wishlist' : wishlist,
        # 'product' : product
    }
    return render(request,'wishlist.html',context)

def add_to_wishlist(request,product_id) :

    product = AddImages.objects.get(id=product_id)
    if Wishlist.objects.filter(product=product).exists():
        messages.error(request,'this product already exist in wishlist')
        return redirect('shop_details',product_id)

    wish_items = Wishlist.objects.create(
        user = request.user ,
        product = product,
    )

    if wish_items :
        messages.success(request,'item added to wishlist succesfully ')
    else :

        messages.error(request,'this is already in the cartttttt.....!')
    
    return redirect('wishlistview')


def remove_item_wishlist(request,wihslist_id) :
    user = request.user
    wish_prod = Wishlist.objects.get(id = wihslist_id,user=user)
    wish_prod.delete()
    messages.success(request,'removed from your wishlist')
    return redirect('wishlistview')

def add_address_checkout(req):

    if req.method == 'POST' :
        print('this is takingggg')
        user = User.objects.get(id=req.user.id)
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
            error_message = 'all fields is required'
            return render(req, 'checkout.html', {'error_message': error_message})
        
        name_pattern = r'^[a-zA-Z]+(?:\s[a-zA-Z]+)*$'
        if not re.match(name_pattern,first_name) :
            error_message['first_name'] = 'first name only the letter and single space'
            return render(req, 'checkout.html', {'error_message': error_message})


        
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
    
def additional_address(req):

    if req.method == 'POST' :
        print('this is takingggg')
        user = User.objects.get(id=req.user.id)
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
            error_message = 'all fields is required'
            return redirect('new_address')        
        name_pattern = r'^[a-zA-Z]+(?:\s[a-zA-Z]+)*$'
        if not re.match(name_pattern,first_name) :
            error_message['first_name'] = 'first name only the letter and single space'
            return redirect('new_address')

        
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
    
    return render(req,'add_address.html')


def add_coupon_to_session(request ,coupon_id) :
    coupon = Coupon.objects.get(id = coupon_id)
    request.session['coupon_applied'] = coupon.is_active
    request.session['coupon_id'] = coupon.id
    request.session['coupon_code'] = coupon.coupon_code
    request.session['coupon_name'] = coupon.coupon_name
    request.session['discount_percentage'] = coupon.discount_percentage
    return redirect(request,'checkout.html')

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
                messages.error(req, 'A coupon has already been applied.')
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

            if sub_total <= coupon.minimum_amnt or sub_total >= coupon.max_amount:
                messages.error(req, f'Your total amount must be between ₹{coupon.minimum_amnt} and ₹{coupon.max_amount} to apply this coupon.')
                return redirect('checkout')

            req.session['coupon_id'] = coupon.id
            req.session['coupon_name'] = coupon.coupon_name
            req.session['coupon_applied'] = True

            messages.success(req, 'Coupon applied successfully.')

            return redirect('checkout')

    messages.error(req, 'Invalid request.')
    return render(req,'checkout.html',{'coupon_applied' : req.session.get('is_applied')  })

from django.db.models import Q
@never_cache
def checkout(req) :

    if req.user.is_authenticated :
        user = req.user
        
        customer = User.objects.get(username = req.user.username)
        cart_items = Cart.objects.filter(user=customer)
        if  not cart_items.exists() :
            messages.error(req, "The Cart is empty.")
            return redirect(cart_view)
        try :   
            Addresses = Address.objects.filter(user=user , is_deleted = False)

        except Address.DoesNotExist :
            pass
        
        subtotal = cart_items.aggregate(sum=Sum('total'))['sum'] or 0
        shipping_fee = 0 if subtotal >= 5000 else 100
        full_total = subtotal + shipping_fee
        discount_amount = 0
        coupon_code = None
        
        available_coupon = Coupon.objects.filter(
            Q(minimum_amnt__lte=full_total) & Q(max_amount__gte=full_total) & Q(is_active=True)
        )[:2]

        if req.session.get('coupon_applied',False) :
            coupon_id = req.session.get('coupon_id')
            coupon = Coupon.objects.filter(id=coupon_id).first()

            if coupon is not None :

                discount_amount = (full_total * coupon.discount_percentage ) / 100
                subtotal -= round(discount_amount)
                full_total -= round(discount_amount)
                coupon_code = coupon.coupon_code


        context = {

            'cart_items' : cart_items,
            'addresses' : Addresses,
            'sub_total' : subtotal,
            'shipping_fee' : shipping_fee,
            'full_total' : full_total,
            'coupon_applied' : req.session.get('is_applied', True),
            'discount_amount' : discount_amount ,
            'coupon_code' : coupon_code,
            'available_coupons' : available_coupon
        }

        return render(req,'checkout.html' , context )
    
    else :
        messages.error(req, 'You need to be logged in to checkout.')
        return redirect('user_login')

def place_order(request) :
    customer = User.objects.get(username = request.user.username)
    cart_items = Cart.objects.filter(user=customer)
    register_user = register.objects.get(user=customer)
    if request.method == 'POST' :
        address_id = request.POST.get('select_address')

        if address_id is None :
            messages.error(request,'please select a address')
            return redirect('checkout')

        address = Address.objects.get(id=address_id)
        pm = request.POST.get('payment_method') 


        if pm is None :
            messages.error(request,'payment method is unavailable')
            return redirect('checkout')
        
        if pm == 'COD' :
        
            customer = User.objects.get(username = request.user.username)
            cart_items = Cart.objects.filter(user=customer)
            register_user = register.objects.get(user=customer)
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
                full_total -= discount_amount
            else:
                applied_coupon = None

                print('this is the discount amounntttt : ',discount_amount)
                print('applied ccoupoonnnn' , applied_coupon)

            order = Order.objects.create (
                register = register_user ,
                address = address,
                payment_method = pm ,
                sub_total = sub_total ,
                shipping_charge = shipping_fee , 
                total = full_total ,
                paid = False ,
                tracking_id = order_id,
                applied_coupen = applied_coupon  ,
                coupon_appliyed = request.session.get('coupon_applied'),
                discount_amount = discount_amount )
            
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

            cart_items.delete()
            
        elif pm == "razorpay" :

            customer = User.objects.get(username = request.user.username)
            cart_items = Cart.objects.filter(user=customer)
            register_user = register.objects.get(user=customer)
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
            request.session['tracking_id'] = order_id
            request.session['total'] = full_total
            request.session['discount_amount'] = discount_amount
            request.session['applied_coupon'] = coupon_id if applied_coupon else None

            return redirect(razorpay_view)
            
            
        print('iam redirtedd successfully')
        return redirect('order_success')
    return redirect('checkout')

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

login_required(login_url='user_login')
@never_cache
def razorpay_view(request):

    if request.user.is_authenticated :
        total = request.session.get('total')
        razorpay_order_id = ''
        order_currency = "INR"

        cart_items = Cart.objects.filter(user=request.user)
        subtotal = cart_items.aggregate(sum=Sum('total'))['sum'] or 0
        shipping_fee = 0 if subtotal >= 5000 else 100

        razorpay_order = client.order.create(dict(amount=int(total * 100), currency=order_currency, payment_capture='0'))
        razorpay_order_id = razorpay_order['id']
        
        register_id = request.session.get('register')
        reg = register.objects.get(id=register_id)

        payment = Payment.objects.create(
            
            amount = total,
            transaction_id=razorpay_order_id,
            paid=False,
            pending=True,
            success=False,
        )

        orders = Order.objects.create(
            register=reg,
            address_id=request.session.get('address_id'),
            tracking_id=request.session.get('tracking_id'),
            payment_method = "Razorpay",
            razorpay_order_id=razorpay_order_id,
            shipping_charge=shipping_fee,
            total=total,
            payment=payment
        )
        
        for item in cart_items :
            items = Order_items.objects.create(
                order = orders ,
                status = 'Order Placed' ,
                product = item.product,
                price = item.product.product.price,
                qnty = item.quantity,
                size = item.sizes.size
            )

            cart_items.delete()

        context = {

            'amount': total,
            'currency': order_currency,
            'order_id': razorpay_order_id,

        }

    return render(request, 'razorpay_summary.html', context)

@never_cache
@csrf_exempt
def payment_success(request):

    if request.method == "POST":
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


        client.utility.verify_payment_signature(params_dict)
        print('my thig is not workingg wellll sucssing ')
        return redirect('success_page')

    return render(request,'order_success.html')

@login_required(login_url='user_login')
def order_details(request, order_id) :
    order = Order.objects.get(id = order_id)
    order_items = Order_items.objects.filter(order=order).order_by('-id')

    context = {

        'order' : order ,
        'order_items' : order_items

    }
    return render(request,'order_details.html',context)

def request_cancel_order_item(req, item_id):
    order_item = Order_items.objects.get(id=item_id)
    if order_item.order.register.user == req.user :
        if req.method == 'POST' :
            cancel_reasons = req.POST.get('cancel_reason')
            order_item.cancel = True
            order_item.status = "Cancelled"
            order_item.cancel_reason = cancel_reasons
            order_item.save()
            return redirect('order_details',order_item.order.id)
    print('cancel form renderedddd')
        
    return render(req,'cancel.html', {'order_item': order_item })

def request_return_order_item(req,item_id) :
    try:
        order_items = Order_items.objects.get(id=item_id)
        print(order_items,'fhksdhkshah')
    except Order_items.DoesNotExist:
        pass
    if req.user.is_authenticated:
        if order_items.order.register.user == req.user and order_items.status == 'Delivered' :
            order_items.request_return = True
            order_items.save()
            messages.success(req,'return request has been submitted')

        else :
            
            messages.error(req,'you can only return products after delivery of items!')
            if order_items :
                return redirect('order_details', order_id = order_items.order.id)
        
    context = {

        'order_items': order_items

    }
        
    return render(req ,'order_details.html',context)

def invoice(request, order_id) :
    if request.user.is_authenticated :
        customer = register.objects.get(user = request.user)
        print(customer)
        try :
            order_items = Order_items.objects.filter(order__id = order_id , order__register = customer)
            print(order_items)
            orders = Order_items.objects.all()

            print('finalee product detaillss ' , orders)

        except register.DoesNotExist :
             messages.error(request,'this product havet reachedd.....!')

    
        total = sum(items.product.product.offer_price * items.qnty for items in order_items )
        context = {

            'order_items' : order_items,
            'customer' : customer,
            'total' : total

        }

        html_string = render_to_string("invoice.html",context)
        config = pdfkit.configuration(wkhtmltopdf="C:\\Users\\Acer\\Desktop\\week9\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

        # generating pdf
        pdf = pdfkit.from_string(html_string, False,configuration=config)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="invoice.pdf"'
        return response
    else:
        return redirect('user_login')