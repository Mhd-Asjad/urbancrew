from . import views
from django.urls import path
urlpatterns = [
    
    path('',views.home,name='home'),
    path('register/',views.reg,name='register'),
    path('user_login/',views.user_login,name='user_login'),
    path('otpvalidation/',views.otp_form,name='otpvalidation'),
    
]