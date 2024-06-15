from django.shortcuts import render, redirect ,get_object_or_404
from django.urls import reverse
from django.http import HttpResponse ,JsonResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.contrib.auth import login, logout, authenticate
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from .models import register
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import re
from .models import *
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.hashers import check_password
from adminapp.models import category
from products.models import *
from cart.models import *
from django.db.models import *

def base(req):
    cat1 = category.objects.all()
    print(cat1)
    context = {"cat1": cat1}
    return render(req, "base.html", context)


@never_cache
def home(
    request
):
    username = request.user.username
    active_offers = Offer.objects.filter(offer_type = 'category' ,is_active = True)
    now = timezone.now()

    for offer in active_offers:
        time_remaining = offer.end_date - now
        offer.time_remaining_days = time_remaining.days
        offer.time_remaining_hours = time_remaining.seconds // 3600
        offer.time_remaining_minutes = (time_remaining.seconds // 60) % 60
        offer.time_remaining_seconds = time_remaining.seconds % 60
        
    context = {

        'offers' : active_offers,
        "username": username
    }
    return render(request, "index.html", context)


@never_cache
@login_required
def reg(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        errors = {}

        username = request.POST.get("username")
        mobile = request.POST.get("mobile")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmpassword = request.POST.get("confirmpassword")

        # Check for missing fields
        if not all([username, mobile, email, password, confirmpassword]):
            messages.error(request, "All fields are required.")
            return redirect("register")

        # Validate password length
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("register")

        # Check for empty trimmed values
        if username.strip() == "" or password.strip() == "":
            errors['username'] = 'Username must not be empty.'
            errors['password'] = 'Password must not be empty.'

        # Validate mobile number length
        if len(mobile) < 10:
            messages.error(request, "Mobile number must be at least 10 digits long.")
            return redirect("register")

        # Validate password and confirmation match
        if password != confirmpassword:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already exists."
            return redirect("register")

        # Password strength checks
        if not any(char.isupper() for char in password):
            print('validd3')
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect("register")

        if not any(char.islower() for char in password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            print('not a valid onee')
            return redirect("register")

        if not any(char in '!@#$%^&*()_+' for char in password):
            print('not a valid oonww2')
            messages.error(request, "Password must contain at least one special character.")
            return redirect("register")

        # If any errors found
        if errors:
            return JsonResponse({'errors': errors})

        # Send OTP and save user data in session
        otp, otp_generated_at = otp_send_to_email(email=email)
        session_for_userdata(request, username, mobile, email, password, otp, otp_generated_at)

        messages.success(request, f"Welcome {username}, please verify OTP")
        return redirect('otpvalidation')

    return render(request, "register.html")

def checkMail(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print('evide nd',email)

    email_exists = User.objects.filter(email=email).exists()
    if email_exists :
        print(email_exists,"igiuyguyfgiyfiyfvihgvfiyfv")
        return JsonResponse({'exist':True})
    else:

        print("nott taked this one before ")
        return JsonResponse({'exist':False})
    

def otp_send_to_email(email):
    otp = random.randint(1000, 9999)
    otp_generated_at = datetime.now().isoformat()
    print('new otp founded :', otp)

    send_mail(
        subject="Welcome! OTP for verification",
        message=f"Your OTP is: {otp}. Please use this OTP to verify your email.",
        from_email="urbancrew144@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return otp, otp_generated_at

def session_for_userdata(request, username, mobile, email, password, otp, otp_generated_at):
    request.session["userlist"] = {
        "username": username,
        "mobile": mobile,
        "email": email,
        "password": password,
        "otp": otp,
        "otp_generated_at": otp_generated_at,
    }

@never_cache
def otp_form(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        otp1 = request.POST.get("otp1")
        otp2 = request.POST.get("otp2")
        otp3 = request.POST.get("otp3")
        otp4 = request.POST.get("otp4")

        full_otp = otp1 + otp2 + otp3 + otp4
        entered_otp = int("".join(full_otp))

        stored_otp = request.session.get("userlist", {}).get("otp")
        user_data = request.session.get("userlist", {})
        otp_generated_at_str = user_data.get("otp_generated_at", "")

        if otp_generated_at_str:
            last_otp_generated = datetime.fromisoformat(otp_generated_at_str)
            current_time = datetime.now()

            if current_time > last_otp_generated + timedelta(minutes=2):
                messages.error(request, "OTP expired, try again!")
                return redirect("otpvalidation")

            print(f"Stored OTP: {stored_otp} ==== Entered OTP: {entered_otp}")

            if str(stored_otp) == str(entered_otp):
                Userotp = User.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                )   

                Userotp.save()
                del request.session["userlist"]
                reg = register.objects.create(user=Userotp, mobile=user_data["mobile"])
                reg.save()
                messages.success(request, "User created successfully")
                return redirect("user_login")
            
            else:
                messages.error(request, "Incorrect OTP")
        else:
            messages.error(request, "OTP data not found. Request a new OTP")

    return render(request, "otpvalidation.html")


def resend_otp(request):
    otp_new = random.randint(1000, 9999)
    otp_generated_at_new = datetime.now().isoformat()
    print(otp_new)

    email = request.session.get("email")

    send_mail(
        subject="welcome otp for verification",
        message=f"Your OTP is : {otp_new}. Please use this OTP to verify your email." ,
        from_email="urbancrew144@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )
    user_data = request.session.get("userlist", {})
    username, mobile, email, password = (
        user_data["username"],
        user_data["mobile"],
        user_data["email"],
        user_data["password"],
    )
    request.session["userlist"] = {
        "username": username,
        "mobile": mobile,
        "email": email,
        "password": password,
        "otp": otp_new,
        "otp_generated_at": otp_generated_at_new,
    }
    print(otp_new)
    return redirect(otp_form)


@never_cache
def user_login(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username, password)

        print("reached near authentication")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            print("passed authentication")
            return redirect("home")

        else:

            messages.error(request, "something went wrong here invalid credential")
            return redirect("user_login")
    else:
        return render(request, "login.html")


def reset_pass_email(req):
    return render(req, "Resetpass/reset_pass_email.html")


def log_out(request):
    logout(request)
    return redirect("home")


# def shop(request):

#     is_authenticated = request.user.is_authenticated
#     # categorys = Product.objects.select_related('categorys').values_list('categorys__name',flat=True).distinct()
#     # print(categorys)

#     return render(request,"shop.html",{"is_authenticated": is_authenticated, "products": products})


def product_list(request):
    categorys = category.objects.filter(is_listed = True )
    is_authenticated = request.user.is_authenticated
    sort_option = request.GET.get('sort')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min', 500)
    max_price = request.GET.get('max', 50000)

    products_query = AddImages.objects.all().order_by('id')

    if category_id :
        products_query = products_query.filter(product__categorys_id=category_id)

    products_query = products_query.filter(product__price__gte = min_price , product__price__lte = max_price)

    if sort_option == 'low_to_high':
        products_query = products_query.order_by('product__price','product_id')
    elif sort_option == 'high_to_low':
        products_query = products_query.order_by('-product__price','product_id')
    elif sort_option == 'A-Z':
        products_query = products_query.order_by('product__product_name','product_id')
    elif sort_option == 'z-a':
        products_query = products_query.order_by('-product__product_name','product_id')


    prod_sum = products_query.aggregate( count = Count('product'))
    tot_count = prod_sum['count']

    return render(request, "shop.html", {"is_authenticated" : is_authenticated, "products": products_query , 'categorys':categorys , 'tot_count' : tot_count})

def shop_details(req, prod_id):
    print('this is ID',prod_id)
    product = AddImages.objects.get(id = prod_id )
    product_offers = Offer.objects.filter(product = product.product,is_active = True)
    variants = AddImages.objects.filter(product__id = product.product.id)
    out_of_stock = [ variant for variant in variants if variant.product.is_available == False]
    sizes = ProductSize.objects.filter(image = product)
    total_stock = sizes.aggregate(total_stock=Sum('stock'))['total_stock'] or 0
    related_products = AddImages.objects.filter(product__categorys = product.product.categorys).exclude(id=prod_id)[:4]
    print(related_products)

    context = {
        
        "product": product ,
        'sizes' : sizes ,
        'variants' : variants,
        'total_stock' : total_stock ,
        'product_offers' : product_offers,
        'related_prods' : related_products,
        'out_of_stock' : out_of_stock

    }

    return render(req, "shop-details.html" , context )

def search_prod(request):
    product_items = AddImages.objects.filter(product__is_deleted=False).order_by('product__product_name')
    
    if request.method == 'GET': 
        query = request.GET.get('query', '')
        if query:

            product_items = product_items.filter(product__product_name__icontains=query)
    return render(request, 'shop.html', {'product_items': product_items})

#----------------------------------------------- starts user_profile --------------------------------------------------------------

@login_required(login_url='user_login')
def user_profile (request , tab = None) :
    if request.user.is_authenticated :
        user = request.user
        try :
            about = register.objects.filter(user = user).first()
        except register.DoesNotExist :
            about = None

    addresses = Address.objects.filter(user=about.user) if about else []
    orders = Order.objects.filter(register__user = user).prefetch_related('order').order_by('-id')

    print(' ordered itemmsss',orders)

    context = {
        'about' : about ,
        'addresses' : addresses,
        'orders' : orders ,
        'tab' : tab or 'v-pills-message' or 'v-pills-profile' ,
    }
    return render(request,'profile.html' , context)

def update_profile(request):
    
    user = request.user
    about = register.objects.filter(user=user).first()

    if request.method == 'POST':
        print('Form submission detected')
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')

        print(f'Received data: username={username}, email={email}, mobile={mobile}, dob={dob}, gender={gender}')

        users = register.objects.filter(user=user).first()

        error_message = {}
        if mobile:
            if not (len(mobile) == 10 and mobile.isdigit()):
                error_message['mobile'] = 'Invalid mobile number. Please enter a 10-digit number.'

            elif register.objects.filter(mobile=mobile).exclude(user=user).exists():
                error_message['mobile'] = 'Mobile number already exists.'

            else:
                users.mobile = mobile

        if email :
            
            if User.objects.filter(email=email).exclude(username=user.username).exists():
                error_message['email'] = 'Email already exists.'
            else:
                users.user.email = email

        if dob:
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                if dob_date >= timezone.now().date():
                    error_message['dob'] = 'update failed Date must be in the past.'
                else:
                    users.dob = dob

            except ValueError:
                error_message['dob'] = 'Invalid date format. Use YYYY-MM-DD.'

        if error_message:
            print('Error_messages', error_message)
            return render(request, 'profile.html', {'about': users, 'error_message': error_message})

        print('No validation errors, proceeding to save')

        if username:
            users.user.username = username
        if email:
            users.user.email = email
        if gender:
            users.gender = gender

        print('Attempting to save user profile')
        users.user.save()
        users.save()
        messages.success(request, 'Profile saved successfully')
        return redirect('user_profile')
    return render(request,'profile.html', {'about': about})


@login_required
def change_pass(req, pass_id):
    if req.user.is_authenticated:
        user = User.objects.filter(id=pass_id).first()
        if user is None:
            messages.error(req, "User not found.")
            return redirect("user_profile")

        if req.method == 'POST':
            current_password = req.POST.get('current_password')
            new_password = req.POST.get('new_password')
            confirm_password = req.POST.get('confirm_password')

            error_message = {}

            if not check_password(current_password, user.password):
                error_message['current_password'] = 'Current password is incorrect.'
                messages.error(req, error_message['current_password'])
                return redirect('change_pass', pass_id=pass_id)

            if new_password != confirm_password:
                error_message['confirm_password'] = 'Passwords do not match.'
                messages.error(req, error_message['confirm_password'])
                return redirect('change_pass', pass_id=pass_id)

            if len(new_password) < 8:
                error_message['new_password'] = 'Password must be at least 8 characters long.'
                messages.error(req, error_message['new_password'])
                return redirect('change_pass', pass_id=pass_id)

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(req, user)
            messages.success(req, "Your password was successfully updated!")
            return redirect("user_profile")

        # customer = register.objects.get(user=user)
        # context = {'user': user, 'customer': customer}
        # return render(req, 'change_password.html', context)
    return redirect('user_login')

def add_address(req) :
    if req.user.is_authenticated :
        user = req.user
        print(user)
        if req.method == 'POST' :
            first_name = req.POST.get('first_name')
            last_name = req.POST.get('last_name')
            email = req.POST.get('email')
            house = req.POST.get('house')
            city = req.POST.get('city')
            state = req.POST.get('state')
            pin_code = req.POST.get('pin_code')
            country = req.POST.get('country')
            mobile_number = req.POST.get('mobile_number')
            
            if not all([ first_name,last_name,email,house,city,state,pin_code,country,mobile_number ]) :
                messages.error(req,'all fields are required')
                return redirect('user_profile_with_tab',tab ='v-pills-messages')
            
            name_pattern = r'^[a-zA-Z]+(?:\s[a-zA-Z]+)*$'
            if not re.match(name_pattern,first_name):
                messages.error(req, 'first name contain only characters or single space')

            if not re.match(name_pattern,last_name) :
                messages.error(req, 'first name contain only characters or single space')

            location_pattern = r'^[a-zA-Z\s]+$'
            if len(mobile_number) < 10 or len(mobile_number) > 12:               
                messages.error(req, "Mobile number is not valid.")
                return redirect("add_address")

            location_pattern = r'^[a-zA-Z\s]+$'
            if not re.match(location_pattern, city):
                messages.error(req, "City name must contain only letters and spaces.")
                return redirect("add_address")

            if not re.match(location_pattern, state):
                messages.error(req, "State name must contain only letters and spaces.")

            if not re.match(location_pattern, country):
                messages.error(req, "Country name must contain only letters and spaces.")

            if not re.match(location_pattern, house):
                messages.error(req, "House name must contain only letters and spaces.")
            
            address = Address.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                house=house,
                city=city,
                state=state,
                pin_code=pin_code,
                country=country,
                mobile_number=mobile_number
            )
            messages.success(req,'adress added')
            return redirect('user_profile_with_tab',tab ='v-pills-messages' )

def edit_address(req,address_id):

    user=req.user
    addresses = Address.objects.filter(user=user).order_by('-id')
    address = get_object_or_404(Address,id=address_id ,user=user)
    if req.method == "POST" and req.user.is_authenticated:
        print(addresses)
        print(user,'this the user for')
        print(address,'this is my address')
        
    
        first_name = req.POST.get('first_name')
        last_name = req.POST.get('last_name')
        email = req.POST.get('email')
        house = req.POST.get('house')
        city = req.POST.get('city')
        state = req.POST.get('state')
        country = req.POST.get('country')
        pin_code = req.POST.get('pin_code')
        mobile_number = req.POST.get('mobile_number')

        if len(mobile_number) < 10 and len(mobile_number) > 12:
            messages.error(req, "Moblie number is not valid.")
            return redirect("edit_address")
        
        address.first_name = first_name
        address.last_name = last_name
        address.email = email
        address.house = house
        address.city = city
        address.state = state
        address.country = country
        address.pin_code = pin_code
        address.mobile_number = mobile_number
        address.save()
        
        messages.success(req, 'Address updated successfully')
        return redirect('user_profile_with_tab', tab = 'v-pills-messages')
    
    return render(req,'edit_address.html', {'address' : address})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def delete_address(request, address_id):
    if request.method == 'POST':
        address = Address.objects.get(id=address_id)
        address.is_deleted = True
        address.save()
        return JsonResponse({'status': 'success'}, status=200)
    return JsonResponse({'status': 'error'}, status=400)

#--------------------------------------------------- profile section ends ------------------------------------------------------------
def order_success(request):
    if request.user.is_authenticated :

        context = {}
        return render(request,'order_success.html' , context)
        # return redirect(reverse('user_profile_with_tab', kwargs={'tab': 'v-pills-profile'}))
    else:
        return redirect('login')
    
    