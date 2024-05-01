from . import views
from django.urls import path
urlpatterns = [
    
    path('',views.home,name='home'),
    
    path('base/',views.base,name='base'),

    path('register/',views.reg,name='register'),
    path('user_login/',views.user_login,name='user_login'),
    path('pass_email/',views.reset_pass_email,name='pass_email'),

    path('otpvalidation/',views.otp_form,name='otpvalidation'),
    path('resentotp/',views.resend_otp,name='resentotp'),
    path('logout/',views.log_out,name='logout'),

    path('shop/',views.shop,name='shop'),
    path('shop_details/<int:prod_id>/',views.shop_details,name='shop_details'),
    
    
]