from django.shortcuts import render, redirect, get_object_or_404
from products.models import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from django.db.models import Sum

# Create your views here.


def add_cart(request):

    if request.method == "POST":
        print('workinngggggg')
        size_id = request.POST.get('size')
        product_id = request.POST.get('product_id')
        product = Product.objects.get(id=product_id)
        size = ProductSize.objects.get(id = size_id)

        print('taking the size')
        if not size_id :
            return JsonResponse({'success': False, 'message': 'Please select a size.'})
        
        if size.stock <= 0:
            messages.error(request, 'The selected size is out of stock.')
            return redirect('shop_details')

        print(product_id,'this is prod id')
        print(size_id,'sizess')

        user = request.user
        print('this my carttttt.!!!',user)
        Cart.objects.create(user=user, product=product , sizes = size , total=product.price,quantity=1)
        messages.success(request, 'Item added to cart successfully.')
        return redirect("cart")
    
    return redirect('cart')
        
def remove_cart(request, cart_id) :
    cart_item = Cart.objects.get(id=cart_id, user=request.user)
    cart_item.delete()
    return redirect("cart")


@login_required(login_url="user_login")
def cart_view(request):
    user = request.user.id
    print('ghhooiii my id',user)
    cart_items = Cart.objects.filter(user=user)

    # print(cart_items, "this is cart items")
    subtotal = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
    subs_amnt = subtotal["sum"]
    print(type(subs_amnt),'i am on ')
    shippingfee = 0
    try:
        if subs_amnt < 5000 :

            shippingfee += 100

            full_total = subs_amnt + shippingfee

        else:

            full_total = subs_amnt
    except TypeError:
            full_total = 0
    print("after update", full_total)

    context = {
        "subtotal": subtotal["sum"],
        "full_total": full_total,
        "cart_items": cart_items,
        "shippingfee": shippingfee,
    }

    return render(request, "cart.html", context)


def update_tot_price(request):
    data = json.loads(request.body)
    cartid = data.get("cartid")
    user = request.user

    if request.method == "POST":
        data = json.loads(request.body)
        if data.get("operation") == "increment":
            quantity = data.get("quantity")
            cartid = data.get("cartid")
            cart_items = Cart.objects.get(id=cartid)
            prod_id = Product.objects.get(id=cart_items.product_id)
            images = AddImages.objects.get(product_id=prod_id.id)
            stock = ProductSize.objects.get(image_id=images.id)
            if quantity <= stock.stock - 1:
                cart_items.quantity += 1
                cart_items.total = prod_id.price * cart_items.quantity
                cart_items.save()
                subtotal = Cart.objects.filter(user_id=user).aggregate(sum=Sum("total"))
                subs_amnt = subtotal["sum"]
                print("this is sub", subtotal)
                print(subs_amnt)
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
                return JsonResponse({"success": False, "message": "notupdated"})
        elif data.get("operation") == "decrease":
            quantity = data.get("quantity")
            cartid = data.get("cartid")
            cart_items = Cart.objects.get(id=cartid)
            prod_id = Product.objects.get(id=cart_items.product_id)
            cart_items.quantity -= 1
            cart_items.total = prod_id.price * cart_items.quantity
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

                },
            )
        

def checkout(req):

    if req.user.is_authenticated :
        user = req.user

        cart_items = Cart.objects.filter(user=user)
        
        
        subtotal = cart_items.aggregate(sum=Sum('total'))['sum'] or 0
        print(subtotal)
        shipping_fee = 0 if subtotal >= 5000 else 100
        full_total = subtotal + shipping_fee



    context = {
        'cart_items' : cart_items,
        'sub_total' : subtotal,
        'shipping_fee' : shipping_fee,
        'full_total' : full_total
    }
    return render(req,'checkout.html' , context)
