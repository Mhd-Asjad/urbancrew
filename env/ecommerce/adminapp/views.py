from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import JsonResponse , HttpResponse
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
from wallet.models import *
from django.utils.crypto import get_random_string
from django.db.models import *
from decimal import Decimal
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import timedelta
import calendar
from io import BytesIO
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404


@never_cache
@login_required(login_url="adminlog")
def dash_view(request):
    product = AddImages.objects.all()
    if request.user.is_superuser:
        selected_month = request.GET.get('month')
        selected_year = request.GET.get('year')

        if not selected_month :
            current_date = datetime.now()
            selected_month = f"{current_date.year}-{current_date.month:02d}"


        orders = Order_items.objects.filter(status="Delivered").select_related('order', 'product').order_by('order__created_at')
        this_year = timezone.now().year
        this_month = timezone.now().month
        monthly_orders = orders.filter(order__created_at__month=this_month)
        month_revenue = monthly_orders.aggregate(month_revenue=Sum(F('price') * F('qnty'), output_field=DecimalField()))['month_revenue']
        
        top_category_month = monthly_orders.values('product__product__categorys__name').annotate(
            total_quantity=Sum('qnty')
        ).order_by('-total_quantity')[:5]

        yearly_orders = orders.filter(order__created_at__year=this_year)
        year_revenue = yearly_orders.aggregate(year_revenue=Sum(F('price') * F('qnty'), output_field=DecimalField()))['year_revenue']
        
        top_category_year = yearly_orders.values('product__product__categorys__name').annotate(
            total_quantity=Sum('qnty')
        ).order_by('-total_quantity')[:5]

        top_category = yearly_orders.values('product__product__categorys__name').annotate(
            total_quantity=Sum('qnty')
        ).order_by('-total_quantity').first()

        top_categories = [{'category': cat['product__product__categorys__name'] , 'total_quantity': cat['total_quantity']} for cat in top_category_year]

        if selected_month :
            year, month = map(int, selected_month.split('-'))
            orders = orders.filter(order__created_at__year=year, order__created_at__month=month)
        elif selected_year:
            year = int(selected_year)
            orders = orders.filter(order__created_at__year=year)

        delivered_orders_per_day = orders.values('order__created_at__date').annotate(
            total_orders=Sum('qnty'),
            total_revenue=Sum(F('price') * F('qnty')),
            product_sold=Count('product__product__product_name')
        ).order_by('order__created_at__date')

        top_five_products = orders.values('product__product__product_name').annotate(
        total_sold=Sum('qnty')
        ).order_by('-total_sold')[:5]

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = {
                'labels': [order['order__created_at__date'].strftime('%Y-%m-%d') for order in delivered_orders_per_day],
                'total_orders': [order['total_orders'] for order in delivered_orders_per_day],
                'total_revenue': [order['total_revenue'] for order in delivered_orders_per_day],
                'product_sold': [order['product_sold'] for order in delivered_orders_per_day],
                'top_five_products_labels': [product['product__product__product_name'] for product in top_five_products],
                'top_five_products_data': [product['total_sold'] for product in top_five_products],
            }
            return JsonResponse(data)

        context = {
            'product': product,
            'month_revenue': month_revenue,
            'year_revenue': year_revenue,
            'top_category_month': top_category_month,
            'top_category_year': top_category_year,
            'top_cats': top_categories,
            'yearly_top' : top_category,
            'selected_month' : selected_month ,
            'selected_year' : selected_year,
            'timezone': timezone,

        }

        return render(request, "dashboard.html", context)

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
            request.session['is_admin'] = True
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Incorrect username or password!!")
            return redirect("adminlog")

    else:
        return render(request, "adminlog.html")


@login_required(login_url="adminlog")
def customer_view(request):
    if request.user.is_superuser :
        users = User.objects.all().order_by("-id")
        return render(request, "customer.html", {"users": users})
    else:
        return redirect('adminlog')


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
    if request.user.is_superuser :

        is_list = category.objects.get(id=category_id)
        is_list.is_listed = True
        is_list.save()
        return redirect("category")
    
    return redirect('adminlog')


def unlist_category(request, category_id):

    if request.user.is_superuser :


        is_unlist = category.objects.get(id=category_id)
        is_unlist.is_listed = False
        is_unlist.save()
        return redirect("category")
    return redirect('adminlog')


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

def order_view(request):
    if request.user.is_superuser:
        return render(request, 'order/order_view.html')
    else:
        messages.error(request, 'Admin can only access this')
        return redirect('adminlog')
    
def fetch_orders(request):
    if request.user.is_superuser:
        search_query = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)
        orders = Order.objects.filter(
            Q(tracking_id__icontains=search_query) |
            Q(register__user__username__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        ).order_by("-id")
        paginator = Paginator(orders, 10) 
        page_obj = paginator.get_page(page_number)

        orders_list = []
        for order in page_obj:
            orders_list.append({
                'tracking_id': order.tracking_id,
                'username': order.register.user.username ,
                'total': order.total,
                'payment_method': order.payment_method,
                'detail_url': f"/ordered_item/{order.id}"  # Adjust URL pattern as needed

            })

        return JsonResponse({
            'orders': orders_list,
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number
        })
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

@user_passes_test(lambda u: u.is_superuser, login_url='adminlog')
def ordered_item(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = Order_items.objects.filter(order=order).order_by('-id')

    if not order_items.exists():
        messages.error(request, 'Order does not exist or has no items.')
        return redirect('order_view')  # Redirect to some admin log page or handle as needed

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'order/order_items.html', context)


def update_order_status(request,order_id):
    order = Order.objects.get(id = order_id)
    if request.method == 'POST'and request.user.is_superuser :
        data = json.loads(request.body)
        item_id = data.get('item_id')
        item = Order_items.objects.get(id = item_id)

        new_status = data.get('status')
        if new_status == 'Cancelled' and not item.cancel :
                return JsonResponse({'error': 'Cannot cancel this item without permission.'}, status=403)
        try:
            order_item = Order_items.objects.get(order = order , id = item_id )

            if new_status and new_status != order_item.status:
                if new_status == 'Returned':
                    order_item.request_return = True
            order_item.status = new_status
            order_item.save()

            return JsonResponse({'success': True})
        except Order_items.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order item not found'} , status =404)
        
    return render(request,'order/order_items.html',{ 'order' : order },status=400)
        

def confirm_return_order_item(request, item_id):
    try:
        # Retrieve the order item using the item_id
        order_item = Order_items.objects.get(id=item_id)
        
        # Check if a return request exists
        if order_item.request_return :
            order_item.status = 'Returned'
            order_item.save()
            messages.success(request, 'Return request has been confirmed.')
        else:
            messages.error(request, 'No return request found for this item.')

        return redirect('ordered_item', order_id=order_item.order.id)
    except Order_items.DoesNotExist:
        messages.error(request, 'Order item not found.')
        return redirect('orders')


def return_refund(request,return_id) :
    try :
        return_item = Order_items.objects.get(id = return_id)
        print(return_id)

    except Order_items.DoesNotExist:
        messages.error(request, "Order item does not exist.")
        return redirect('ordered_item')
    
    order = return_item.order
    if return_item.request_return == True and return_item.status == 'Returned' and return_item.order.payment_method != "COD" :

        total_discount = order.discount_amount if order.coupon_appliyed else 0
        total_amount = 0
        total_amount = order.total
        print(total_amount,'this is my total amount@@@@@@@')
        print(total_discount, 'wallet offer pricee')
        total_quantity = Order_items.objects.filter(order = order).aggregate(total_quantity = Sum('qnty'))['total_quantity']
        discount_per_item = Decimal(total_discount) / Decimal(total_quantity)
        print('discount forr per itemmm !!!' ,discount_per_item)
        original_price = return_item.product.product.offer_price if return_item.product.product.offer_price else return_item.product.product.price
        print('og pricee:',original_price)
        refunt_amount = 0

        discount_return_item =  discount_per_item * Decimal(return_item.qnty)
        non_returned_items_count = Order_items.objects.filter(order=order).exclude(status__in=['Cancelled', 'Refunded']).count()

        if non_returned_items_count > 1 :    
            if original_price < order.total :
                refunt_amount = (original_price - discount_return_item) * Decimal(return_item.qnty)
                order.total -= refunt_amount

        else :
            refunt_amount = order.total
        
        print(order.total ,'after refund') 
        print('refund amount with shipping fee :',refunt_amount)
        print('count afterr!!',non_returned_items_count)
        order.save()

        product_size = ProductSize.objects.get(image = return_item.product , size = return_item.size)
        product_size.stock += return_item.qnty
        product_size.save()

        user = order.register.user
        wallet , created = Wallet.objects.get_or_create(user=user)
        wallet.balance += refunt_amount
        wallet.save()

        tranc_id = "Re_" + get_random_string(6,'ABCPMOZ456789')
        if Wallet_transactions.objects.filter(transaction_id = tranc_id).exists() :
            tranc_id = "Re_" + get_random_string(6,'ABCPMOZ456789' )
            print(tranc_id,'this is the second one')

        Wallet_transactions.objects.create(

            wallet = wallet,
            type = 'Refund' ,
            amount = refunt_amount,
            transaction_id = tranc_id,
            description = 'Rerturn refund',
            time_stamp = timezone.now()
        )

        if return_item.request_return and not return_item.cancel :
            return_item.refund_processed = True
            return_item.status = 'Refunded'
            return_item.order.status = 'Returned',
            return_item.save()
            messages.success(request,f'AMOUNT of ₹{refunt_amount} added to {return_item.order.register.user.username} wallet ')
            return redirect('ordered_item', order_id = order.id)
    else :  
        messages.error(request, "alreadyy refundedd")
        return redirect('ordered_item',order_id = order.id)
    
    


#-----------------------------------------------------coupon management------------------------------------------------------------
#view coupon
login_required(login_url='adminlog')
def view_coupon(request) :
    if request.user.is_superuser :
        cup = Coupon.objects.all()

        context = {

            'cup' : cup

        }
        return render(request,'coupon/coupon.html',context)
    else :
        return redirect('adminlog')

#add couponnnn
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
    else: 
        return redirect('adminlog')

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
        return redirect('adminlogin')


def del_coupon(request,coupon_id) :
    if request.user.is_superuser :
        coupon = Coupon.objects.get(id = coupon_id)
        coupon.delete()
        messages.success(request,'coupon deleted')
        return redirect('view_coupon')
    else :
        return redirect('user_login')


def sales_report(request):
    if request.user.is_superuser:
        if request.method == 'GET':
            from_date = request.GET.get("from")
            to_date = request.GET.get("to")
            month = request.GET.get("month")
            year = request.GET.get("year")

            order = Order_items.objects.filter(
                cancel=False,
                request_return=False,
                status='Delivered'
            ).order_by('order__created_at')

            filters = {}

            if from_date :
                filters['from_date'] = from_date
                order = order.filter(order__created_at__gte=from_date)

            if to_date:
                filters['to_date'] = to_date
                order = order.filter(order__created_at__lte=to_date)

            if month:
                year, month = map(int, month.split("-"))
                order = order.filter(order__created_at__year=year, order__created_at__month=month)

            if year:
                filters['year'] = year
                order = order.filter(order__created_at__year=year)

            request.session['filters'] = filters

            print(request.session.get('filters'),'adffdsdataaaaaaaaaaaa')

            count = order.count()
            total = order.aggregate(total=Sum('order__total'))["total"]
            total_discount = order.aggregate(total_discount=Sum('order__discount_amount'))['total_discount']

            request.session['total_sale_count'] = count
            request.session['overall_amount'] = total
            request.session['total_discount_amount'] = total_discount



            context = {
                "order": order,
                'count': count,
                'total': total,
                'total_discount': total_discount
            }

            return render(request, 'sales_report.html', context)
        else:
            messages.error(request, 'Invalid request method.')
            return redirect('adminlog')
    else:
        messages.error(request, 'You have no permission to access this page.')
        return redirect('adminlog')


def generate_report(request):
    if request.user.is_superuser:
        filters = request.session.get("filters", {})
        print(filters,'newwwwwwwwwwwwwwww datat')
        sales_data = Order_items.objects.filter(
            cancel=False,
            request_return=False,
            status="Delivered"
        )

        if "from_date" in filters:
            sales_data = sales_data.filter(order__created_at__gte=filters["from_date"])
        if "to_date" in filters:
            sales_data = sales_data.filter(order__created_at__lte=filters["to_date"])
        if "month" in filters:
            year, month = map(int, filters["month"].split("-"))
            sales_data = sales_data.filter(order__created_at__year=year, order__created_at__month=month)
        if "year" in filters:
            sales_data = sales_data.filter(order__created_at__year=filters["year"])

        overall_sales_count = request.session.get("total_sale_count")
        overall_order_amount = request.session.get("overall_amount")
        overall_discount = request.session.get("total_discount_amount")

        total_products = sales_data.aggregate(total_quantity=Count("product__product__product_name"))["total_quantity"] or 0
        total_revenue = sales_data.aggregate(total_amount=Sum("order__total"))["total_amount"] or 0

        if "format" in request.GET and request.GET["format"] == "pdf":
            return generate_pdf_report(sales_data, overall_sales_count, overall_order_amount, overall_discount)

        elif "format" in request.GET and request.GET["format"] == "excel":
            return generate_excel_report(sales_data, total_products, total_revenue)

        return redirect("sales_report")
    else:
        return redirect("admin_login")

def generate_pdf_report(sales_data, overall_sales_count, overall_order_amount, overall_discount):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    centered_style = ParagraphStyle(name="Centered", parent=styles["Heading1"], alignment=1)

    today_date = datetime.now().strftime("%Y-%m-%d")
    content = []

    company_details = f"<b>URBAN CREW </b><br/>Email: urbancrew144@example.com<br/>Date: {today_date}"
    content.append(Paragraph(company_details, styles["Normal"]))
    content.append(Spacer(1, 0.5 * inch))

    content.append(Paragraph("<b>SALES REPORT</b><hr>", centered_style))
    content.append(Spacer(1, 0.5 * inch))

    data = [["Order ID", "Product", "Quantity", "Total Price", "Date"]]
    for sale in sales_data:
        formatted_date = sale.order.created_at.strftime("%a, %d %b %Y")
        data.append([
            sale.order.tracking_id,
            sale.product.product.product_name,
            sale.qnty,
            sale.product.product.offer_price,
            formatted_date,
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    content.append(table)
    content.append(Spacer(1, 0.5 * inch))

    overall_sales_count_text = f"<b>Overall Sales Count:</b> {overall_sales_count}"
    overall_order_amount_text = f"<b>Overall Order Amount:</b> {overall_order_amount}"
    overall_discount_amount_text = f"<b>Overall Discount:</b> {overall_discount}"

    content.append(Paragraph(overall_sales_count_text, styles["Normal"]))
    content.append(Paragraph(overall_order_amount_text, styles["Normal"]))
    content.append(Paragraph(overall_discount_amount_text, styles["Normal"]))

    doc.build(content)

    current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    file_name = f"Sales_Report_{current_time}.pdf"

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'

    return response

def generate_excel_report(sales_data, total_products, total_revenue):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Sales Report")

    bold = workbook.add_format({'bold': True})
    money_format = workbook.add_format({'num_format': '#,##0.00'})

    headings = ["Order ID", "Billing Name", "Date", "Total", "Payment Method", "Product Name"]
    header_format = workbook.add_format({"bold": True})
    for col, heading in enumerate(headings):
        worksheet.write(0, col, heading, bold)

    row = 1
    for item in sales_data:
        worksheet.write(row, 0, item.order.tracking_id)
        worksheet.write(row, 1, item.order.register.user.username)
        worksheet.write(row, 2, item.order.created_at.strftime("%d-%m-%Y"))
        worksheet.write(row, 3, item.order.total, money_format)
        worksheet.write(row, 4, item.order.payment_method)
        worksheet.write(row, 5, f"{item.product.product.product_name} ({item.product.color}) {item.size}")
        row += 1

    worksheet.write(row + 1, 0, "Total Products:", bold)
    worksheet.write(row + 1, 1, total_products, bold)
    worksheet.write(row + 2, 0, "Total Revenue:", bold)
    worksheet.write(row + 2, 1, total_revenue, money_format)
    workbook.close()

    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    current_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    file_name = f"Sales_Report_{current_time}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'

    return response