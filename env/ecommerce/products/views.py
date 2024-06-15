from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib import messages
from adminapp.models import category
from django.views.generic.edit import CreateView, UpdateView
from django.forms import ValidationError
from django.contrib.auth import logout
from django.http import Http404,JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


# from django.urls import reverse_lazy


@never_cache
@login_required(login_url="adminlog")
def view_product(request):
    if request.user.is_superuser:
        products = Product.objects.all().order_by("id")
        return render(request, "product.html", {"products": products})
    else:
        return redirect("adminlog")

@login_required(login_url="adminlog")
def add_product(req):
    if req.user.is_superuser:

        categories = category.objects.all()
        size_add = ProductSize.objects.all()

    if req.method == "POST":
        product_name = req.POST.get("name")
        price = req.POST.get("price")
        c_id = req.POST.get("cat")
        image_upload = req.FILES.get("image")

        if not product_name or not price or not c_id or not image_upload :
            messages.error(req, "Please fill in all the required fields.")
            return redirect("addproduct")
        if product_name.isspace():
            messages.error(req, "not taken only white spaces!")
            return redirect("addproduct")
    
        price = float(price)
        if price <= 0:
            messages.error(req, "give a valid price format!!")
            return redirect("addproduct")

        if Product.objects.filter(product_name__iexact=product_name).exists():
            messages.error(req, "This product already exists!")
            return redirect("addproduct")

        try:
            selected_category = category.objects.get(id=c_id)

        except category.DoesNotExist:
            messages.error(req, "Selected category does not exist.")
            return redirect("addproduct")

        new_product = Product.objects.create(
            product_name=product_name,
            price=price,
            categorys=selected_category,
            img=image_upload,
        )
        new_product.save()
        return redirect("dashboard")

    return render(req, "addproducts.html", {"categories": categories, "size_add": size_add})


def add_variant(req,product_id) :
    pro = Product.objects.get(id = product_id)
    print()
    if req.method == "POST" :

        color = req.POST.get("color")
        image1 = req.FILES.get("image1")
        image2 = req.FILES.get("image2")
        image3 = req.FILES.get("image3")
        Ssmall = req.POST.get("ssmall")
        smedium = req.POST.get("smedium")
        slarge = req.POST.get("slarge")
        sxlarge = req.POST.get("sxlarge")

        prod_id = product_id
        print(prod_id,'this is the id of the product')
        if not color :
            messages.error(req,'this field is requiredd')
            return redirect('addvariant',prod_id)
        
        if AddImages.objects.filter(color__iexact = color , product = prod_id ).exists():
            messages.error(req,'this color variant already createdd!!')
            return redirect('addvariant',prod_id)

        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif' ,'avif', 'webp']
        for image in [image1,image2,image3] :
            if image and not image.name.split('.')[-1].lower() in allowed_extensions:
                messages.error(req, 'Only image files are allowed (jpg, jpeg, png, gif ,avif ).')
                return redirect('addvariant',prod_id)
        print(Ssmall ,smedium,slarge)
        print(type(Ssmall))

        if not Ssmall and not smedium and not slarge and not sxlarge :
            messages.error(req,'give atleast stock for one size')
            return redirect('addvariant',prod_id)
        
        sizes = {'S': Ssmall, 'M': smedium, 'L': slarge, 'XL': sxlarge}
        
        for size, stock in sizes.items():
            if stock is not None and stock != '' :
                try:
                    stock_value = int(stock)
                    if stock_value < 0:
                        messages.error(req, 'Stock values must be non-negative.')
                        return redirect('addvariant', product_id)
                except ValueError:
                    messages.error(req, 'Stock values must be valid integers.')
                    return redirect('addvariant', product_id)

        product_img = AddImages.objects.create(product=pro, color=color, image1=image1, image2=image2, image3=image3)

        sizes = {'S': Ssmall, 'M': smedium, 'L': slarge, 'XL' : sxlarge }
        for size,stock in sizes.items() :
            
            if stock is not None :

                stock_value = int(stock) if stock.isdigit() and int(stock) >= 0 else 0

            ProductSize.objects.create(image = product_img , product_id = pro, size = size , stock = stock_value)


        product_img.save()
        messages.success(req, "variants added successfully.")
        return redirect('show_variants',product_id)

    return render(req, "addvariant.html", {"pro" : pro})


def showvariants(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = AddImages.objects.filter(product=product).order_by('id')
    sizes = ProductSize.objects.filter(product_id=product)
    context = {
        'product': product,
        'variants': variants,
        "sizes": sizes
    }
    return render(request, 'variant.html', context)

def edit_size(req, color_id):
    if req.user.is_superuser:
        color = get_object_or_404(AddImages, id=color_id)
        for size_id, stock in req.POST.items():
            if size_id.startswith('size_'):
                size_id = size_id.replace('size_', '')
                
                try:
                    product_size = ProductSize.objects.get(id=size_id, image=color)
                    product_size.stock = stock
                    product_size.save()
                    messages.success(req, "Product size edited successfully")
                except ProductSize.DoesNotExist:
                    messages.error(req, f"Product size with ID {size_id} does not exist.")
                    return redirect('show_variants', product_id=color.product.id)

        return redirect('show_variants', product_id=color.product.id)
    
    else:
        messages.error(req, "You do not have permission to edit sizes.")
        return redirect('admin_log')



def edit_variant(request, product_id):
    variant = get_object_or_404(AddImages, id=product_id)
    if request.method == "POST":
        color = request.POST.get('color')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        if AddImages.objects.filter(color__iexact = color , id = variant.id).exists():
            messages.error(request,'this color have already taken')
            return redirect('editvariant',product_id = variant.id)
        variant.color = color
        if image1:
            variant.image1 = image1
        if image2:
            variant.image2 = image2
        if image3:
            variant.image3 = image3
        variant.save()
        messages.success(request, 'variant Successfully updated')
        return redirect('show_variants', product_id=variant.product.id)

    context = {
        'variant': variant
    }
    return render(request, 'edit_variant.html', context)

def valid_color(request) :
    color = request.GET.get('color')
    product_id = request.GET.get('product_id')
    variant_id = request.GET.get('variant_id')

    is_taken = AddImages.objects.filter(color__iexact = color ,product_id = product_id ).exclude(id=variant_id).exists()
    return JsonResponse({'is_taken':is_taken})

def active(request , variant_id):
    if request.user.is_superuser :
        if variant_id :
            print(variant_id)
            variant = AddImages.objects.get(id = variant_id)
            print(variant)
            variant.is_active = True
            variant.save()
            prod_id = variant.product.id
            messages.success(request,f' {variant} variant listedd')
            return redirect('show_variants', prod_id)
        
    return redirect('adminlog')

def deactivate(request,variant_id):
    if request.user.is_superuser:
        if variant_id:
            variant = AddImages.objects.get(id = variant_id)
            variant.is_active = False
            variant.save()
            variant_id = variant.product.id
            messages.success(request, f" {variant} Product has been Unlisted")
            return redirect('show_variants', variant_id)
        else:
            messages.error(request, "The variant id is not correct!!")
            return redirect("show_variants")
    
    messages.warning(request, 'You are not an admin!!')
    return redirect('adminlog')
def del_variant(req, variant_id):
    add_image = AddImages.objects.get(id = variant_id)
    product = Product.objects.get(images__id = variant_id)
    add_image.delete()
    messages.success(req, "Variant deleted successfully.")
    return redirect('show_variants',product.id)

# def addsize(req):
#     addImages = AddImages.objects.all()
#     if req.method == "POST":
#         color = req.POST.get("color")
#         prod_size = req.POST.get("size")
#         stock = req.POST.get("stock")
#         img_id = req.POST.get("img")

#         if not color and not prod_size and not stock or not img_id:
#             messages.error(req, "select a product and Please fill out all fields.")
#             return redirect("addsize")

#         try:

#             stock = int(stock)
#             if stock < 0:
#                 raise ValueError("Stock must be a positive integer.")
            
#         except ValueError:

#             messages.error(req, "Invalid stock value. Please enter a positive integer.")
#             return redirect("addsize")
        
#         add_color = AddImages.objects.get(id=img_id)
#         if ProductSize.objects.filter(image__product = add_color.product,size=prod_size).exists():
#             print(prod_size)
#             messages.error(req, "size already exists for this product.")
#             return redirect("addsize")
        
#         if not any( size in 'M,S,XL,L' for size in prod_size ):
#             messages.error(req,'give a valid size format')
#             return redirect('addsize')
#         print(add_color,add_color.product.id)

#         prod = Product.objects.get(id = add_color.product.id)
#         print(prod)
#         prod_details = ProductSize.objects.create(image=add_color, size=prod_size, stock=stock ,product_id = prod)
#         prod_details.save
#         messages.success(req, "size added")

#     return render(req, "addsize.html", {"add_color": addImages})


def delete_prod(req, product_id):

    try:

        product = Product.objects.get(id=product_id)
        product.delete()
        messages.success(req, "product deleted succesfully")
        return redirect("product")

    except Exception as e:

        messages.error(req, str(e))
        return redirect("product")


def list_prod(request, product_id):
    prods = Product.objects.get(id=product_id)
    prods.is_available = True
    prods.save()
    return redirect("product")


def unlist_prod(request, product_id):
    prods = Product.objects.get(id=product_id)
    prods.is_available = False
    prods.save()
    return redirect("product")


@never_cache
@login_required(login_url="adminlog")
def edit_prod(request, product_id):
    print("product id",product_id)

    try:
        products = Product.objects.get(id = product_id)
        if not products:
            messages.error(request, "Product images not found.")
            return redirect("edit_prod", product_id)
        categories = category.objects.all()
    except Product.DoesNotExist:
        raise Http404("Product does not exist")
    if request.method == "POST":
        name = request.POST.get("product_name")
        price = request.POST.get("price")
        cat_id = request.POST.get("category")
        thumb_img = request.FILES.get("thumbnail")

        if not name.strip() :
            messages.error(request, "Product name cannot be empty or contain only whitespace")
            return redirect("edit_prod", product_id)

        try:
            price = float(price)
            if price <= 0:
                messages.error(request, "Give a valid price format")
                return redirect("edit_prod", product_id)
            
        except ValueError:
            messages.error(request, "Price must be a valid number")
            return redirect("edit_prod", product_id)
        
        products.product_name = name
        products.price = price
        products.categorys = category.objects.get(id=cat_id)
        if thumb_img:
            products.img = thumb_img
       
        try:
            products.save()
            messages.success(request, "Product has been edited successfully.")
            return redirect("product")
        
        except Exception as e:
            messages.error(request, f"An error occurred while updating the product: {e}")
            return redirect("edit_prod", product_id)

    context = {
        "products": products, 
        "categories": categories
    }

    return render(request, "product_edit.html", context)

def search_results(request):

    query = request.GET.get("query")
    results = AddImages.objects.filter(product__product_name__icontains=query)

    print(query)
    print(results)
    return render(request, "search.html", {"products": results, "query": query})




def log_out(request):
    logout(request)
    return redirect("adminlog")
