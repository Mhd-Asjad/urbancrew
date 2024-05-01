from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from .models import category
import re
from datetime import datetime
from django.views.decorators.cache import never_cache

@never_cache
def dash_view(request) :
    if request.user.is_superuser:
        return render(request,'dashboard.html')
    return redirect('adminlog')

@never_cache
def adminlog(request):
        if request.user.is_superuser:
            return redirect('dashboard')
        
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            print(username, password)

            user = authenticate(request, username=username, password=password)
            print(user)

            if user is not None and user.is_superuser:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Incorrect username or password!!')
                return redirect('adminlog')

        else:

            return render(request, 'adminlog.html')

@login_required(login_url='adminlog')
def customer_view(request) :

    users = User.objects.all().order_by('id')
    return render(request,'customer.html',{'users' : users})


def user_block(request, user_id):

    user = User.objects.get(id = user_id)
    user.is_active = False
    user.save()
    return redirect(customer_view)
    
def user_unblock(request, user_id):
    user = User.objects.get(id = user_id)
    user.is_active = True
    user.save()
    return redirect(customer_view)

@login_required(login_url='adminlog')
def category_view(request) :
    if request.user.is_superuser:
        cat = category.objects.filter(is_deleted=False).order_by('name')
        return render(request,'category.html',{'cat' : cat})
    
    else :

        return redirect('adminlog')

@never_cache
def sf_delete_cat(request,category_id):
    try :

        print(category_id)
        cat1 = category.objects.get(id=category_id)
        cat1.is_deleted = True
        cat1.save()
        return redirect('trash')
    
    except Exception as e :
        messages.error(request, str(e))
        return redirect('category')

@never_cache
@login_required(login_url='adminlog')
def restore_cat (request,category_id):
    try :

        cat1 = category.objects.get(id=category_id)
        cat1.is_deleted = False
        cat1.save()
        return redirect('category')
    
    except Exception as e:
        messages.error(request,str(e))
        return redirect('category')

@never_cache
@login_required(login_url='adminlog')
def add_category(request) :
    if request.method == 'POST' :

        name = request.POST.get('name')
        description = request.POST.get('description')

        if category.objects.filter(name=name).exists():
            messages.error(request,'catogory already exists')
            # return redirect('addcategory')
                        
        else :

            categorys = category.objects.create(name=name,description=description)
            categorys.save()
            messages.success(request,'category added sucessfully')

    return render(request, 'add_category.html')

@login_required(login_url='adminlog')
def edit_category (request,category_id):
    data = category.objects.get(id=category_id)

    if request.method == 'POST' :
        name = request.POST.get('name')
        description = request.POST.get('description')

        data.name=name 
        data.description=description
        data.save()
        messages.success(request,'category updated ')
        return redirect('category')
        
    return render(request,'edit_cat.html',{'data' : data})

def list_category(request,category_id):

    is_list = category.objects.get(id = category_id)
    is_list.is_listed = True
    is_list.save()
    return redirect('category')

def unlist_category (request,category_id):

    is_unlist = category.objects.get(id=category_id)
    is_unlist.is_listed = False
    is_unlist.save()
    return redirect('category')

@login_required(login_url='adminlog')
def trash (request) :
    cat = None
    try:

        if request.user.is_superuser :
            cat = category.objects.filter(is_deleted=True).order_by('name')
           
        
        if cat not in cat :
            messages.error(request, "No items found in the recycle bin.")

    except Exception as e :
        messages.error(request,str(e))
        return redirect('adminlog')

    
    return render(request,'trash.html', {'cat': cat} )

def trash_remove (request,category_id) :
    try :
        categorys = category.objects.get(id=category_id)
        categorys.delete()
        return redirect('trash')
    
    except Exception as e :
        messages.error(request,str(e))
        return redirect('trash')


def log_out(request):

    logout(request)
    return redirect('adminlog')

def greet_based_on_time(request):
    now = datetime.now()

    if now.hour < 12:
        message = "Good morning"

    elif now.hour < 18:
        message = "Good afternoon"

    else:
        message = "Good evening"

    return render(request, 'nav.html', {'message': message})