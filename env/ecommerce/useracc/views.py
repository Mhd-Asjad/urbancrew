from django.shortcuts import render,redirect
from django.shortcuts import render, redirect 
from django.http import HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.contrib.auth import login,logout,authenticate
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .models import * 
import re
# Create your views here.

def home (request):
    return render(request,'index.html')

def reg (req) :
    if req.method == 'POST' :

        username = req.POST.get('username')
        mobile = req.POST.get('phone')
        email = req.POST.get('email')
        password = req.POST.get('password')
        confirmpassword = req.POST.get('confirmpassword')
        
        if not all([username,mobile,email,password,confirmpassword]) :
            messages.error(req,'please fill up all the feilds')
            return redirect('register')

        if username.isspace() or password.isspace():
            messages.error (req,'not taken only have white spaces')
            return redirect('register')
        
        if len(password) < 4:
            messages.error(req, 'Password must be at least 4 char long.')
            return redirect('register')
        
        if len(mobile) < 10 :
            messages.error(req,'give valid phone number')

        if password != confirmpassword :
            messages.error(req, 'Passwords do not match')
            return redirect('register')

        if User.objects.filter(username = username).exists():
            error_message ="This username is already taken."
            return render(req,'register.html',{'error_message' : error_message} )

        if User.objects.filter(email=email).exists():
            messages.error(req,'This email is already taken.')
            return redirect('register')
        
        if not any(char.isupper() for char in password) :
            messages.error(req,'password contain atleast one uppercase character')
            return redirect('register')
        
        if not any(char.islower() for char in password) :
            messages.error(req,'password must contains altleast one lowercase')
            return redirect('register')
        
        otp,otp_generated_at = otp_send_to_email(email)
        session_for_userdata(req,username,mobile,email,password,otp,otp_generated_at)
        messages.success(req,f'welcome user {username}')
        return redirect('otpvalidation')       
        
    return render(req,'register.html')

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

        return otp, otp_generated_at
def session_for_userdata(request,username,phone,email,password,otp,otp_generated_at):

    request.session['userlist'] ={

        'username' : username,
        'phone' : phone ,
        'email' : email,
        'password' : password,
        'otp' : otp ,
        'otp_generated_at' : otp_generated_at

    }

def otp_form (request):

    return render(request,'otpvalidation.html')

def user_login(request):

    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        print(email,password)
        user = authenticate(request,email=email,password=password)
        
        if user is not None:
            login(request, user)
            return render(request,'home.html')
        
        else:

            messages.error(request, 'Invalid Credentials')
            return redirect('user_login')
                 
    return render(request,'login.html')

def log_out(request) :
    
    logout(request,User)