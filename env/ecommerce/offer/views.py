from django.shortcuts import render , redirect

from .models import *
from products.models import *
from adminapp.models import category
from django.views.decorators.cache import never_cache, cache_control
from django.contrib import messages
from datetime import datetime , timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse



# Create your views here.

def view_offers(request) :
    if request.user.is_superuser :
        offers = Offer.objects.all()

        return render(request,'view_offer.html',{'offers':offers})
    

    else :


        return render('admin_log')

@never_cache
def add_offer(request) :
    if request.user.is_superuser :
        today = timezone.now()
        products = Product.objects.all()
        categories = category.objects.all()

        if request.method == 'POST' :

            offer_type = request.POST.get('offer_type')
            category_id = request.POST.get('category')
            product_id = request.POST.get('product')
            disc = request.POST.get('discount_percentage')
            end_date = request.POST.get('end_date')

            if not offer_type :
                messages.error(request,'select a offer type')
                return redirect('add_offer')

            try:
                disc = float(disc)
            except ValueError:
                messages.error(request, 'Invalid percentage value')
                return redirect('add_offer')
            
            if disc <=5 or disc > 75 :
                messages.error(request, 'Give a valid percentage between 5 and 75')
                return redirect('add_offer')
            
            if offer_type == 'category' :
                if Offer.objects.filter(categorys__id = category_id).exists():
                    messages.error(request,'already added')
                    return redirect('add_offer')
                
                cat = category.objects.get(id = category_id)

                Offer.objects.create(

                    offer_type = Offer.CATEGORY,
                    categorys = cat ,
                    percentage = disc ,
                    end_date = end_date
                )

                messages.success(request,'offer added succesfully')
                return redirect('view_offer')
            elif offer_type == 'product' :
                if Offer.objects.filter(product__id = product_id).exists():
                    messages.error(request,'this alreaddy added!')
                    return redirect('add_offer')
                end_date = timezone.datetime.strptime(end_date,"%Y-%m-%d").date()
                if str(end_date) < str(today) :
                    messages.error(request,'date cannot be in the past!!')
                    return redirect('add_offer')
                
                prod = Product.objects.get(id = product_id)
                Offer.objects.create(
                    offer_type = Offer.PRODUCT,
                    product = prod ,
                    percentage = disc,
                    end_date = end_date 
                )
                messages.success(request,'offer added successfully')
            return redirect('view_offer')
        
    return render(request,'add_offers.html',{ 'products' : products , 'categories' : categories})

def edit_offer(request ,offer_id) :

    if request.user.is_authenticated and request.user.is_superuser:
        today = timezone.now()
        offer = get_object_or_404(Offer, id = offer_id )

        print(offer)
        products = Product.objects.all()
        categories = category.objects.all()
        
        if request.method == 'POST':
            offer_type = request.POST.get('offer_type')
            category_id = request.POST.get('category')
            product_id = request.POST.get('product')
            discount_percentage = request.POST.get('discount_percentage')
            end_date = request.POST.get('end_date')
            
            try:

                disc = float(discount_percentage)
            except ValueError:

                messages.error(request, 'Invalid percentage value')
                return redirect('add_offer')
            
            if disc < 5 or disc > 75 :
                messages.error(request, 'Give a valid percentage between 5 and 75')
                return HttpResponseRedirect(reverse('edit_offer', args=[offer_id]))  

            if offer_type == 'category':
                
                if Offer.objects.filter(categorys__id=category_id).exclude(id=offer_id).exists():
                    messages.error(request, "Offer already exists for this category.")
                    return HttpResponseRedirect(reverse('edit_offer', args=[offer_id]))
                category_instance = get_object_or_404(category, id=category_id)
                offer.offer_type = Offer.CATEGORY
                offer.category = category_instance

            end_date = timezone.datetime.strptime(end_date,"%Y-%m-%d").date()
            if str(end_date) < str(today) :
                messages.error(request,'date cannot be in the past!!')
                return HttpResponseRedirect(reverse('edit_offer', args=[offer_id]))

            elif offer_type == 'product':
            
                if Offer.objects.filter(product__id=product_id).exclude(id=offer_id).exists():
                    messages.error(request, "Offer already exists for this product.")
                    return HttpResponseRedirect(reverse('edit_offer', args=[offer_id])) 
                product = Product.objects.get(pk=product_id)
                offer.offer_type = Offer.PRODUCT
                offer.product = product
            
            offer.percentage = round(disc)
            offer.end_date = end_date
            offer.save()
            messages.success(request, "Offer updated successfully.")
            return redirect('view_offer')

        return render(request, 'edit_offer.html', {'offer': offer, 'products': products, 'categories': categories})
    else:
         return redirect("adminlogin")        

def active_offers(request,id):
    offer = get_object_or_404(Offer,pk = id)
    if offer.is_active == False :
        offer.is_active = True
        offer.save()

    else :
        offer.is_active = False
        offer.save()
    return redirect('view_offer')