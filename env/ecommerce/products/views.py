from django.shortcuts import render,redirect,reverse
from .models import *
from django.contrib import messages
from adminapp.models import category
from django.views.generic.edit import CreateView, UpdateView
from django.forms import ValidationError
from django.contrib.auth import logout
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache




# from django.urls import reverse_lazy



# Create your views here.
@never_cache
@login_required(login_url='adminlog')
def view_product(request):
    if request.user.is_superuser :

        products = AddImages.objects.all().order_by('id')
        return render(request,'product.html',{'products' : products})
    else :

        return redirect('adminlog')

@login_required(login_url='adminlog')
def add_product(req):
    if req.user.is_superuser :

        categories = category.objects.all()
        size_add = ProductSize.objects.all()

    if req.method == 'POST':
        product_name = req.POST.get('name')
        price = req.POST.get('price')
        c_id = req.POST.get('cat')
        image_upload = req.FILES.get('image')

        if not product_name or not price or not c_id or not image_upload:
            messages.error(req, 'Please fill in all the required fields.')
            return redirect('addproduct')
        if product_name.isspace():
            messages.error(req,'not taken only white spaces!')
            return redirect('addproduct')           
        
        price = float(price)
        if price <= 0 :
            messages.error(req,'give a valid price format')
            return redirect('addproduct')

        if Product.objects.filter(product_name__iexact=product_name).exists():
            messages.error(req, 'This product already exists.')
            return redirect('addproduct')

        try:
            selected_category = category.objects.get(id=c_id)

        except category.DoesNotExist:
            messages.error(req, 'Selected category does not exist.')
            return redirect('addproduct')

        new_product = Product.objects.create(
            product_name=product_name,
            price=price,
            categorys =selected_category,
            img = image_upload
        )

        new_product.save()
        return redirect('addimage')
    
    return render(req, 'addproducts.html', {'categories': categories, 'size_add' : size_add } )



def add_image(req):
        product = Product.objects.all()

        if req.method == 'POST' :

            color = req.POST.get('color')
            image1 = req.FILES.get('image1')
            image2 = req.FILES.get('image2')
            image3 = req.FILES.get('image3')
            prod_id=req.POST.get('prd')

            products=Product.objects.get(id=prod_id)

            product_img =  AddImages.objects.create(product=products,color=color,image1=image1,image2=image2,image3=image3)
            product_img.save()
            messages.success(req, 'Product added successfully.')

        return render(req,'addimage.html',{'product':product})

def addsize (req):
    addImages = AddImages.objects.all()
   

    if req.method == 'POST' :
        color = req.POST.get('color')
        prod_size = req.POST.get('size')
        stock = req.POST.get('stock')
        img_id = req.POST.get('img')
        

        if not color and not prod_size and not stock or not img_id :
            messages.error(req, 'select a product and Please fill out all fields.')
            return redirect('addsize')

        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError("Stock must be a positive integer.")
        except ValueError:
            messages.error(req, 'Invalid stock value. Please enter a positive integer.')
            return redirect('addsize')

        if ProductSize.objects.filter(size=prod_size).exists():
            messages.error(req, 'size already exists for this product.')
            return redirect('addsize')

        add_color = AddImages.objects.get(id=img_id)

        prod_details = ProductSize.objects.create(image=add_color,size=prod_size,stock=stock)
        prod_details.save
        messages.success(req,'size added')

    return render(req,'addsize.html',{'add_color' : addImages})

def delete_prod(req,product_id):

    try :
        product = Product.objects.get(id=product_id)
        product.delete()
        messages.success(req,'product deleted succesfully')
        return redirect('product')


    except Exception as e :

        messages.error(req,str(e))
        return redirect('product')
    

def list_prod(request,product_id):
    prods = Product.objects.get(id=product_id)
    prods.is_available = True
    prods.save()
    return redirect('product')

def unlist_prod(request,product_id):
    prods = Product.objects.get(id=product_id)
    prods.is_available = False
    prods.save()
    return redirect('product')
@never_cache
@login_required(login_url='adminlog')
def edit_prod(request, product_id):
    try :

        products = Product.objects.get(id=product_id)
        images = products.images.all()
        categories = category.objects.all()

    except Product.DoesNotExist:
        
        raise Http404("Product does not exist")


    if request.method == 'POST':
        name = request.POST.get('product_name')
        price = request.POST.get('price')
        cat_id = request.POST.get('category')
        color = request.POST.get('color')
        thumb_img = request.FILES.get('thumbnail')
        img1 = request.FILES.get('image1')  
        img2 = request.FILES.get('image2')
        img3 = request.FILES.get('image3')

        if not name.strip():

            messages.error(request, 'Product name cannot be empty or contain only whitespace')
            context = {

                'product': products,
                'categories': categories,
                'images': images
            }

            return render(request,'product_edit.html', context)
        



        
        price= float(price)
        if price <= 0 :

            messages.error(request,'give a valid price format')
            context = {
                'product': products,
                'categories': categories,
                'images': images
            }

            return render(request, 'product_edit.html', context)
            
        if thumb_img:
                products.img = thumb_img


        products.product_name = name
        products.price = price
        products.categorys.name = cat_id
        
        
        products.save()


        for img in images:

            img.color = color
            img.image1 = img1
            img.image2 = img2
            img.image3 = img3

            img.save()
        

        messages.success(request,'Product has been edited successfully.')
        return redirect('product')

    context = {
        'product': products,
        'categories': categories,
        'images': images
    }

    return render(request, 'product_edit.html',context)

def search_results(request):

    query = request.GET.get('query')
    results = AddImages.objects.filter(product__product_name__icontains=query)
    print(query)
    print(results)
    return render(request, 'search.html', {'products': results , 'query': query})

def log_out(request):

    logout(request)
    return redirect('adminlog')