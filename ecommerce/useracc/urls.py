from . import views
from django.urls import path
from django.conf.urls import handler404

handler404 = views.custom_404

urlpatterns = [
    path("", views.home, name="home"),
    path("base/", views.base, name="base"),
    path("register/", views.reg, name="register"),
    path("user_login/", views.user_login, name="user_login"),
    path("resset_password/", views.reset_pass_email, name="reset_password"),
    path("reset_password_otp_form/",views.reset_password_otp_form,name='reset_password_otp_form'),
    path("password/",views.reset_password,name='password'),

    path("otpvalidation/", views.otp_form, name="otpvalidation"),
    path("resentotp/", views.resend_otp, name="resentotp"),
    path("logout/", views.log_out, name="logout"),
    path('shop/',views.product_list,name='shop'),
    path("shop_details/<int:prod_id>/", views.shop_details, name="shop_details"),
    path("shop_search/",views.search_prod,name='shop_search'),
    path('order_success/',views.order_success,name='order_success'),
    path("user_profile/",views.user_profile,name="user_profile"),
    path('profile/<str:tab>/', views.user_profile,name='user_profile_with_tab'),
    path("update_profile",views.update_profile,name='update_profile'),
    path('change_pass/<int:pass_id>/',views.change_pass,name='change_pass'),
    path("add_address/",views.add_address,name='add_address'),
    path("edit_address/<int:address_id>/",views.edit_address,name="edit_address"),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),

    # path('validate_email/',views.validate_email, name='validate_email'),
    # path("checkmail/",views.checkMail,name="checkMail")
]
