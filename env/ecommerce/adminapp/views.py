from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import category
import re
from datetime import datetime
from django.utils import timezone
from django.views.decorators.cache import never_cache
from cart.models import *


@never_cache
def dash_view(request):
    if request.user.is_superuser:
        return render(request, "dashboard.html")
    return redirect("adminlog")


@never_cache
def adminlog(request):

    if request.method == "POST" :
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username,password)

        user = authenticate(request, username=username, password=password)
        print(user)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Incorrect username or password!!")
            return redirect("adminlog")

    else:

        return render(request, "adminlog.html")


@login_required(login_url="adminlog")
def customer_view(request):
    users = User.objects.all().order_by("id")
    return render(request, "customer.html", {"users": users})


def user_block(request, user_id):

    user = User.objects.get(id=user_id)
    user.is_active = False
    user.save()
    return redirect(customer_view)


def user_unblock(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = True
    user.save()
    return redirect(customer_view)


@login_required(login_url="adminlog")
def category_view(request):
    if request.user.is_superuser:
        cat = category.objects.filter(is_deleted=False).order_by("name")
        return render(request, "category/category.html", {"cat": cat})

    else:

        return redirect("adminlog")


@never_cache
def sf_delete_cat(request, category_id):
    try:

        print(category_id)
        cat1 = category.objects.get(id=category_id)
        cat1.is_deleted = True
        cat1.save()
        return redirect("trash")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("category")


@never_cache
@login_required(login_url="adminlog")
def restore_cat(request, category_id):
    try:

        cat1 = category.objects.get(id=category_id)
        cat1.is_deleted = False
        cat1.save()
        return redirect("category")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("category")


@never_cache
@login_required(login_url="adminlog")
def add_category(request):
    if request.method == "POST":

        name = request.POST.get("name")
        description = request.POST.get("description")

        if category.objects.filter(name__iexact = name).exists():
            messages.error(request, "catogory already exists")
            return redirect('addcategory')

        else:

            categorys = category.objects.create(name=name, description=description)
            categorys.save()
            messages.success(request, "category added sucessfully")

    return render(request, "category/add_category.html")


@login_required(login_url="adminlog")
def edit_category(request, category_id):
    data = category.objects.get(id=category_id)

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        data.name = name
        data.description = description
        data.save()
        messages.success(request, "category updated successfuly")
        return redirect("category")

    return render(request, "category/edit_cat.html", {"data": data})


def list_category(request, category_id):

    is_list = category.objects.get(id=category_id)
    is_list.is_listed = True
    is_list.save()
    return redirect("category")


def unlist_category(request, category_id):

    is_unlist = category.objects.get(id=category_id)
    is_unlist.is_listed = False
    is_unlist.save()
    return redirect("category")


@login_required(login_url="adminlog")
def trash(request):
    cat = None
    try:

        if request.user.is_superuser:
            cat = category.objects.filter(is_deleted=True).order_by("name")

        if cat not in cat:
            messages.error(request, "No items found in the recycle bin.")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("adminlog")

    return render(request, "category/trash.html", {"cat": cat})


def trash_remove(request, category_id):
    try:
        categorys = category.objects.get(id=category_id)
        categorys.delete()
        return redirect("trash")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("trash")


def log_out(request):

    logout(request)
    return redirect("adminlog")


def greet_based_on_time(request):
    now = datetime.now()

    if now.hour < 12:
        message = "Good morning"

    elif now.hour < 18:
        message = "Good afternoon"

    else:
        message = "Good evening"

    return render(request, "nav.html", {"message": message})

def order_view(request) :
    
    orders = Order.objects.all().order_by("-id")



    context = {

        'orders' : orders
    }

    return render(request,'order/order_view.html',context)


def ordered_item(request , order_id) :

    order = Order.objects.get(id=order_id)

    order_items = Order_items.objects.filter(order = order)

    context = {
        
        'order' : order ,
        'order_items' : order_items

    }

    

    return render(request,'order/order_items.html',context)


def update_order_status(request, order_id):
    order = Order.objects.get(id = order_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        new_status = data.get('status')
    
        try:
            order_item = Order_items.objects.get(order = order , id = item_id )

            if new_status and new_status != order_item.status:
                if new_status == 'Returned':
                    order_item.request_return = True
            order_item.status = new_status
            order_item.save()

            return JsonResponse({'success': True})
        except Order_items.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order item not found'})
        
    return render(request,'order/order_items.html',{ 'order' : order })
        

def confirm_return_order_item(request, item_id):
    try:
        # Retrieve the order item using the item_id
        order_item = Order_items.objects.get(id=item_id)
        
        # Check if a return request exists
        if order_item.request_return:
            order_item.status = 'Returned'
            order_item.save()
            messages.success(request, 'Return request has been confirmed.')
        else:
            messages.error(request, 'No return request found for this item.')

        return redirect('ordered_item', order_id=order_item.order.id)
    except Order_items.DoesNotExist:
        messages.error(request, 'Order item not found.')
        return redirect('orders')  


#-----------------------------------------------------coupon management------------------------------------------------------------
#manage coupon
def view_coupon(request) :
    cup = Coupon.objects.all()

    context = {

        'cup' : cup

    }
    return render(request,'coupon/coupon.html',context)

def add_coupon(request):
    if request.user.is_superuser :
        today = timezone.now()
        if request.method == 'POST' :
            code = request.POST.get('coupon_code')
            name = request.POST.get('coupon_name')
            disc = request.POST.get('discount_percentage')
            min_amount = request.POST.get('minimum_amnt')
            max_amount = request.POST.get('max_amount')
            expiry_date = request.POST.get('expiry_date')

            if not all([code,name,disc,min_amount,max_amount]) :
                messages.error(request,'all field is requied ')
                return redirect('add_coupon')

            if Coupon.objects.filter(coupon_code = code,coupon_name = name).exists():
                messages.error(request,'coupon already exists')
                return redirect('add_coupon')
            try :
                disc = float(disc)
                if disc < 10 or disc > 100 :
                    messages.error(request,'percentage should be between 10 and 100')
                    return redirect('add_coupon')

            except ValueError :
                    messages.error(request, "Please enter a valid discount percentage.")
                    return redirect("add_coupon")

            min_amount = float(min_amount)
            max_amount = float(max_amount)
            if max_amount < min_amount :
                messages.error(request,'min values must be big value')
                return redirect('add_coupon')

            if max_amount < 120 or min_amount < 10 :
                messages.error(request,'value must be positive integer at leat 120')
                return redirect('add_coupon')

            expiry_date = timezone.datetime.strptime(expiry_date,"%Y-%m-%d").date()
            if str(expiry_date) < str(today) :
                messages.error(request,'date cannot be in the past')
                return redirect('add_coupon')
            
            elif str(expiry_date) == str(today) :
                messages.error(request,'the expiry_date not set it today!!!!')
                return redirect('add_coupon')
            Coupon.objects.create(
                coupon_code = code ,
                coupon_name=name ,
                discount_percentage = disc , 
                minimum_amnt = min_amount,
                max_amount = max_amount,
                expiry_date = expiry_date )
            messages.success(request,'coupon created succesfully')
            return redirect('view_coupon')
    
    return render(request,'coupon/add_coupon.html')

def edit_coupon(request,coupon_id) :
    if request.user.is_superuser :
        cpn = Coupon.objects.get(id = coupon_id)
        if request.method == 'POST' :
            Coupon_code = request.POST.get('coupon_code')
            Coupon_name = request.POST.get('coupon_name')
            Discount_Percentage = request.POST.get('discount_percentage')

            min_amount = request.POST.get('minimum_amnt')
            max_amount = request.POST.get('max_amount')
            expiry_date =request.POST.get('expiry_date')

            if Coupon_name :

                if not Coupon_name.strip() :
                    messages.error(request,'name cant put as emty')
                    return redirect('edit_coupon',coupon_id = coupon_id)
                
                cpn.coupon_name = Coupon_name
            
            if Discount_Percentage :
                if float(Discount_Percentage) < 10 or float(Discount_Percentage) > 100 :
                    messages.error(request,'percentage should be b/w 10 and 100')
                    return redirect('edit_coupon',coupon_id = coupon_id)
            cpn.discount_percentage = Discount_Percentage

            if not Coupon_code.strip() :
                messages.error(request,'put a valid coupon name')
                return redirect('edit_coupon',coupon_id = coupon_id)
            cpn.coupon_code = Coupon_code

            if min_amount :
                cpn.minimum_amnt = min_amount

            if max_amount :
                cpn.max_amount = max_amount

            if expiry_date :
                cpn.expiry_date = expiry_date

            cpn.save()
            messages.success(request,'coupon edited')
            return redirect('view_coupon')
        return render(request,'coupon/edit_coupon.html',{ 'cpn' : cpn })
    else :
        messages.error(request,'super user only can access to this')
        return redirect('adminlog')


def del_coupon(request,coupon_id) :
    if request.user.is_superuser :
        coupon = Coupon.objects.get(id = coupon_id)
        coupon.delete()
        messages.success(request,'coupon deleted')
        return redirect('view_coupon')
    else :
        return redirect('user_login')
