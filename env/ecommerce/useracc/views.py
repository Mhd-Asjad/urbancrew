from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.contrib.auth import login,logout,authenticate
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime , timedelta
from .models import register
from datetime import timezone
import re
from . models import register
from django.contrib.auth.hashers import make_password
from adminapp.models import category
from products.models import *

def base (req):
    cat1 = category.objects.all()
    print(cat1)
    context = {
        'cat1' : cat1
    }
    return render(req,'base.html' , context)

@never_cache
def home (request,):
    username = request.user.username
    # product = AddImages.objects.get(id=prod_id)
    return render(request,'index.html',{'username' : username})


@never_cache
def reg (request) :
    if request.user.is_authenticated :
        return redirect('home')
    
    if request.method == 'POST' :
        username = request.POST.get('username')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmpassword = request.POST.get('confirmpassword')
        
        # if len(password) < 6 :
        #     messages.error(request, 'Password must be at least 6 char long.')
        #     return redirect('register')
        
        # if username.strip() == '' or password.strip() == '' :
        #     messages.error(request,'username only contains white spaces')
        #     return redirect('register')
        
        # if len(mobile) < 10 :
        #     messages.error(request,'give valid phone number')
        #     return redirect('register')
        
        # if password != confirmpassword :
        #     messages.error(request, 'Passwords do not match')
        #     return redirect('register')

        # if User.objects.filter(username = username).exists():
        #     messages.error(request,'The username already used')
        #     return redirect('register')

        # if User.objects.filter(email=email).exists():
        #     messages.error(request,'This email is already taken.')
        #     return redirect('register')
        
        # if not any(char.isupper() for char in password) :
        #     messages.error(request,'password contain atleast one uppercase character')
        #     return redirect('register')
        
        # if not any(char.islower() for char in password) :
        #     messages.error(request,'password must contains altleast one lowercase')
        #     return redirect('register')
        
        otp,otp_generated_at = otp_send_to_email(email = email)
        session_for_userdata(request,username,mobile,email,password,otp,otp_generated_at)
        messages.success(request,f'welcome {username} verify otp' )
        return redirect('otpvalidation')
    
    return render(request,'register.html')

def otp_send_to_email (email):

    otp = random.randint(1000,9999)
    otp_generated_at = datetime.now().isoformat()
    print(otp)  

    send_mail(

        subject='welcome otp for verification',
        message=f'Your OTP is : {otp}. Please use this OTP to verify your email.',
        from_email = 'urbancrew144@gmail.com',
        recipient_list=[email],
        fail_silently=False
    )

    return otp,otp_generated_at

def session_for_userdata(request,username,mobile,email,password,otp,otp_generated_at):
    request.session['userlist'] ={

        'username' : username,
        'mobile' : mobile,
        'email' : email,
        'password' : password,
        'otp' : otp ,
        'otp_generated_at' : otp_generated_at
    }

@never_cache
def otp_form (request):

    if request.user.is_authenticated :
        return redirect('home')

    if request.method == 'POST' :

        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2')
        otp3 = request.POST.get('otp3')
        otp4 = request.POST.get('otp4')

        full_otp = otp1 + otp2 + otp3 + otp4
        entered_otp = int(''.join(full_otp))

        stored_otp = request.session.get('userlist',{}).get('otp')
        user_data = request.session.get('userlist',{})
        otp_generated_at_str = user_data.get('otp_generated_at','')

        if otp_generated_at_str :
            last_otp_generated = datetime.fromisoformat(otp_generated_at_str)
            current_time = datetime.now()

            if current_time > last_otp_generated + timedelta(minutes=2) :
                messages.error(request,'otp got expired try again !!')
                return redirect('otpvalidation')
            
            if str(stored_otp) == str(entered_otp) :
                Userotp = User.objects.create_user(username=user_data['username'],email=user_data['email'],password=user_data['password'])
                Userotp.save()
                del request.session['userlist']
                reg = register.objects.create(user=Userotp,mobile=user_data['mobile'])
                reg.save()
                messages.success(request,"user created sucesfully")
                return redirect('user_login')
        
            else:
                messages.error(request,'incorrect otp')
        else :
            messages.error(request,'otp data not found.request a new otp')

    return render(request,'otpvalidation.html')

def resend_otp(request) :

    otp_new = random.randint(1000,9999)
    otp_generated_at_new = datetime.now().isoformat()
    print(otp_new)
    email = request.session.get('email')

    send_mail (

        subject='welcome otp for verification',
        message=f'Your OTP is : {otp_new}. Please use this OTP to verify your email.',
        from_email = 'urbancrew144@gmail.com',
        recipient_list=[email],
        fail_silently=False
    )
    user_data = request.session.get('userlist',{})
    username,mobile,email,password = user_data['username'],user_data['mobile'],user_data['email'],user_data['password']
    request.session['userlist'] ={

        'username' : username,
        'mobile' : mobile,
        'email' : email,
        'password' : password,
        'otp' : otp_new ,
        'otp_generated_at' : otp_generated_at_new
    }
    print(otp_new)
    return redirect(otp_form)

@never_cache

def user_login(request) :
  
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username,password )

        print('reached near authentication')

        user = authenticate(request, username=username, password=password)
        if user is not None :
            auth.login(request,user)
            print('passed authentication')
            return redirect('home')
        
        else :

            messages.error(request, 'something went wrong here invalid credential')
            return redirect('user_login')
    else :
        return render(request, 'login.html')
    
def reset_pass_email(req):
    
    return render(req,'Resetpass/reset_pass_email.html')
    

def log_out(request):
    logout(request)
    return redirect('home')


def shop(request):
    is_authenticated = request.user.is_authenticated
    products =AddImages.objects.select_related('product').distinct('product')
    print(products)
    # context = {'products': products}

    return render(request, 'shop.html',{'is_authenticated' : is_authenticated , 'products': products} )

def shop_details(req,prod_id):

    product = AddImages.objects.get(id=prod_id )


    return render(req,'shop-details.html',{'product' : product })

