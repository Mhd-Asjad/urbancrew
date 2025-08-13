from django.shortcuts import render, redirect ,get_object_or_404
from django.urls import reverse
from django.http import HttpResponse ,JsonResponse, HttpResponseNotFound
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
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


def base(req) :
    cat1 = category.objects.all()
    context = {"cat1": cat1}
    return render(req, "base.html", context)


@never_cache
def home(
    request
):
    username = request.user.username
    active_offers = Offer.objects.filter(offer_type = 'category' ,is_active = True)

    context = {

        "username": username
    }
    return render(request, "index.html", context)


@never_cache
def reg(request):
    if request.method == "POST":
        errors = {}

        username = request.POST.get("username")
        mobile = request.POST.get("mobile")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmpassword = request.POST.get("confirmpassword")

        if not all([username, mobile, email, password, confirmpassword]):
            errors['general'] = "All fields are required."

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("register")

        if username.strip() == "" or password.strip() == "":
            errors['username'] = 'Username must not be empty.'
            errors['password'] = 'Password must not be empty.'

        if User.objects.filter(username__iexact = username).exists():
            messages.error(request,'username already existsss')
            return redirect('register')

        if len(mobile) < 10:
            messages.error(request, "Mobile number must be at least 10 digits long.")
            return redirect("register")

        if password != confirmpassword:
            messages.error(request, "Passwords do not match.")
            return redirect("register")


        if User.objects.filter(username=username).exists():
            errors['username'] = 'username already existss'
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already exists."

        if not any(char.isupper() for char in password):
            messages.error(request, "Password must contain at least one uppercase letter")
            return redirect("register")

        if not any(char.islower() for char in password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect("register")

        if not any(char in '!@#$%^&*()_+' for char in password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("register")

        # If any errors found
        if errors:
            return JsonResponse({'errors': errors} , status=400)

        # Send OTP and save user data in session
        otp, otp_generated_at = otp_send_to_email(email=email)
        session_for_userdata(request, username, mobile, email, password, otp, otp_generated_at)

        messages.success(request, f"Welcome {username}, please verify OTP")
        return redirect('otpvalidation')

    return render(request, "register.html")

def otp_send_to_email(email):
    otp = random.randint(1000, 9999)
    otp_generated_at = datetime.now().isoformat()

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
    if request.method == "POST":
        otp1 = request.POST.get("otp1")
        otp2 = request.POST.get("otp2")
        otp3 = request.POST.get("otp3")
        otp4 = request.POST.get("otp4")

        full_otp = otp1 + otp2 + otp3 + otp4

        if full_otp.isdigit():
            entered_otp = int(full_otp)

            user_data = request.session.get("userlist", {})
            stored_otp = user_data.get("otp")
            otp_generated_at_str = user_data.get("otp_generated_at")

            if otp_generated_at_str:
                last_otp_generated = datetime.fromisoformat(otp_generated_at_str)
                current_time = datetime.now()

                if current_time > last_otp_generated + timedelta(minutes=2):
                    messages.error(request, "OTP expired, try again!")
                    return redirect("otpvalidation")

                if str(stored_otp) == str(entered_otp):
                    Userotp = User.objects.create_user(
                        username=user_data["username"],
                        email=user_data["email"],
                        password=user_data["password"],
                    )
                    Userotp.save()

                    phone = user_data["mobile"]
                    reg = register(user=Userotp, mobile=str(phone))
                    reg.save()

                    messages.success(request, "User created successfully")
                    return redirect("user_login")
                else:
                    messages.error(request, "Incorrect OTP")
            else:
                messages.error(request, "OTP data not found. Request a new OTP")
        else:
            messages.error(request, 'Invalid OTP. Please enter a valid 4-digit OTP.')
            return redirect('otpvalidation')

    return render(request, "otpvalidation.html")



def resend_otp(request):
    otp_new = random.randint(1000, 9999)
    otp_generated_at_new = datetime.now().isoformat()
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
    return redirect(otp_form)

@never_cache
def user_login(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and not user.is_superuser :
            if 'is_admin' in request.session:
                del request.session['is_admin']
            login(request, user)
            return redirect("home")

        else:

            messages.error(request, "something went wrong here invalid credential")
            return redirect("user_login")
    else:
        return render(request, "login.html")


def reset_pass_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = random.randint(1000, 9999)
            otp_generated_at = datetime.now().isoformat()
            request.session["reset_password_otp"] = {
                "otp": otp,
                "otp_generated_at": otp_generated_at,
                "user_id": user.id ,
                'email' : email

            }
            
            send_mail(
                subject="Password Reset OTP",
                message=f"Your OTP for password reset is: {otp}",
                from_email="urbancrew144@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            
            messages.success(request, "OTP sent to your email address.")
            return redirect('reset_password_otp_form')
        
        except User.DoesNotExist:
            messages.error(request, "Email address not registered.")
    
    return render(request,"Resetpass/reset_pass_email.html")

def reset_password(request) :
    if request.method == "POST":
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        if password and password == password_confirm:
            user_id = request.session.get("user_id_for_reset")
            if user_id :
                user = get_object_or_404(User, id=user_id)
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password reset successful. Please log in with your new password.")
                return redirect("user_login")
            else:
                messages.error(request, "Password reset failed. Please try again.")
                return redirect("password")
        else:
            messages.error(request, "Passwords do not match.")
    
    return render(request, "Resetpass/reset_password.html")

from django.utils.timezone import make_aware

@never_cache
def reset_password_otp_form(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        if otp.isdigit():
            user_data = request.session.get("reset_password_otp", {})
            stored_otp = user_data.get("otp")
            otp_generated_at_str = user_data.get("otp_generated_at")

            if otp_generated_at_str:
                last_otp_generated = datetime.fromisoformat(otp_generated_at_str)
                last_otp_generated = make_aware(last_otp_generated)
                current_time = timezone.now()

                if current_time > last_otp_generated + timedelta(minutes=2):
                    messages.error(request, "OTP expired, try again!")
                    return redirect("reset_pass_email")

                if str(stored_otp) == str(otp):
                    request.session["user_id_for_reset"] = user_data.get("user_id")
                    return redirect("password")
                else:
                    messages.error(request, "Incorrect OTP")
            else:
                messages.error(request, "OTP data not found. Request a new OTP")
        else:
            messages.error(request, 'Invalid OTP. Please enter a valid 4-digit OTP.')
    
    return render(request, "Resetpass/otpform.html")

def log_out(request):
    logout(request)
    return redirect("home")

from django.core.paginator import Paginator

def product_list(request):
    categorys = category.objects.filter(is_listed=True)
    is_authenticated = request.user.is_authenticated

    search_query = request.GET.get('query')
    sort_option = request.GET.get('sort')
    category_id = request.GET.get('category')
    color = request.GET.get('color')
    min_price = request.GET.get('min', 0)
    max_price = request.GET.get('max', 50000)

    products_query = AddImages.objects.filter(is_active=True).order_by('id')
    colors = AddImages.objects.values_list('color', flat=True).distinct()

    if search_query :
        products_query = products_query.filter(product__product_name__icontains = search_query)

    if category_id:
        products_query = products_query.filter(product__categorys__id=category_id)

    if color :
        products_query = products_query.filter(color = color)
    if min_price and max_price :
        products_query = products_query.filter(
            Q(product__offer_price__gte=min_price, product__offer_price__lte=max_price) | Q(product__price__gte=min_price, product__price__lte=max_price))
        
    if sort_option == 'low_to_high':
        products_query = products_query.order_by('product__offer_price')
    elif sort_option == 'high_to_low':
        products_query = products_query.order_by('-product__offer_price')
    elif sort_option == 'A-Z':
        products_query = products_query.order_by('product__product_name')
    elif sort_option == 'Z-A':
        products_query = products_query.order_by('-product__product_name')

    paginator = Paginator(products_query, 9)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    now = timezone.now()
    category_offers = Offer.objects.filter(offer_type = Offer.CATEGORY,categorys__in = categorys , is_active = True , end_date__gt = now)
    product_offers = Offer.objects.filter(
        offer_type=Offer.PRODUCT,
        product__in=[p.product for p in products_query],
        is_active=True,
        end_date__gt=now

    )
    
    offers = {}
    for offer in category_offers :
        offers[f"category_{offer.categorys.id}"] = offer
    for offer in product_offers :
        offers[f"product_{offer.product.id}"] = offer

    return render(request, "shop.html", {
        "is_authenticated": is_authenticated,
        "products": products_page,
        "categorys": categorys,
        "tot_count": paginator.count,
        "prods" : products_query , 
        'colors' : colors,
        'offers' : offers
    })

def shop_details(req, prod_id):
    today = timezone.now()
    
    try :
        
        product = get_object_or_404(AddImages,id = prod_id )

    except AddImages.DoesNotExist : 

        return HttpResponseNotFound("Product not found")
    
    images = product.image1 ,product.image1 , product.image3
    additional_images = product.additional_images if product.additional_images else []
    product_offers = Offer.objects.filter(product = product.product,is_active = True)
    variants = AddImages.objects.filter(product__id = product.product.id)
    out_of_stock = [ variant for variant in variants if variant.product.is_available == False]
    sizes = ProductSize.objects.filter(image = product)
    total_stock = sizes.aggregate(total_stock=Sum('stock'))['total_stock'] or 0
    related_products = AddImages.objects.filter(product__categorys = product.product.categorys).exclude(id=prod_id)[:4]
    valid_offers = Offer.objects.filter(product = product.product , end_date__lte = today , is_active = True)

    context = {

        "product": product ,
        'sizes' : sizes ,
        'variants' : variants,
        'total_stock' : total_stock ,
        'product_offers' : product_offers,
        'related_prods' : related_products,
        'out_of_stock' : out_of_stock ,
        'valid_offers' : valid_offers,
        'additional_images' : additional_images

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
    orders = Order.objects.filter(register__user = user).prefetch_related('order_items').order_by('-id')
    orders = [order for order in orders if order.status != 'Pending' or order.order_items.exists()]

    context = {
        'about' : about ,
        'addresses' : addresses,
        'orders' : orders ,
        'tab' : tab or 'v-pills-home',
    }
    return render(request,'profile.html' , context)

def update_profile(request):
    
    user = request.user
    about = register.objects.filter(user=user).first()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')


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
                messages.warning(request,'email already exists')
            else:
                users.user.email = email

        if dob:
            try:
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
                if dob_date >= timezone.now().date():
                    messages.error(request,'date cannot be in the past')
                    return redirect('user_profile')
                else:
                    users.dob = dob

            except ValueError:
                error_message['dob'] = 'Invalid date format. Use YYYY-MM-DD.'

        if error_message:
            return render(request, 'profile.html', {'about': users, 'error_message': error_message})

        if username:
            users.user.username = username
        if email:
            users.user.email = email
        if gender:
            users.gender = gender

        users.user.save()
        users.save()
        messages.success(request, 'Profile saved successfully')
        return redirect('user_profile')
    return render(request,'profile.html', {'about': about})

@login_required(login_url='user_login')
def change_pass(req, pass_id):
    if req.user.id != pass_id :
        messages.error(req, "You can only change your own password.")
        return redirect("user_profile")
    user = User.objects.filter(id=pass_id).first()
    if user is None:
        messages.error(req, "User not found.")
        return redirect("user_profile")

    if req.method == 'POST':
        current_password = req.POST.get('current_password')
        new_password = req.POST.get('new_password')
        confirm_password = req.POST.get('confirm_password')


        if not check_password(current_password, user.password) :
            messages.warning(req,'Current password is incorrect.')
            return redirect('change_pass', pass_id=pass_id)

        if new_password != confirm_password:
            messages.error('Passwords do not match.')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(req, user)
        messages.success(req, "Your password was successfully updated!")
        return redirect("user_profile")
    return redirect('user_profile')

def add_address(req) :
    if req.user.is_authenticated :
        user = req.user

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
        return redirect('user_profile_with_tab' , tab = 'v-pills-message')
    return JsonResponse({'status': 'error'}, status=400)
#--------------------------------------------------- profile section ends ------------------------------------------------------------

@never_cache
def order_success(request,tab=None):
    if request.user.is_authenticated :

        context = {

            'tab' : tab or 'v-pills-profile'
        }
        return render(request,'order_success.html' , context)
        # return redirect(reverse('user_profile_with_tab', kwargs={'tab': 'v-pills-profile'}))
    else:
        return redirect('login')
    

def custom_404(request, exception):
    return render(request, 'custom_404.html', status=404)