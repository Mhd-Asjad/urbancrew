from django.urls import path
from . import views

urlpatterns = [

    path("cart/", views.cart_view, name="cart"),
    path("add_cart/", views.add_cart, name="add_cart"),
    path("update_quantity/", views.update_tot_price, name="update_quantity"),
    path("remove_cart/<int:cart_id>/", views.remove_cart, name="remove_cart"),

    path('apply_coupon/',views.apply_coupon,name='apply_coupon'),
    path('add_coupon_to_session/<int:product_id>/', views.add_coupon_to_session, name='add_coupon_to_session'),

    path('checkout/',views.checkout,name='checkout'),
    # path('add_address_checkout/',views.add_address_checkout,name='add_address_checkout'),
    path('new_address/',views.additional_address,name='new_address'),

    path('place_order/',views.place_order,name='place_order'),
    path('razorpay_order_summary/',views.razorpay_view,name="razorpay_order_summary"),
    # path('verify-payment/', views.verify_payment, name='verify_payment'),

    path('order_details/<int:order_id>/',views.order_details,name='order_details'),
    path('change_shipping_address/<int:order_id>/', views.change_shipping_address, name='change_shipping_address'),
    path('cancel_order_item/<int:item_id>/',views.cancel_order_item,name='cancel_order_item'),
    path('cancel_refund/<int:cancel_id>/', views.cancel_refund, name='cancel_refund'),
    path('request_return_order_item/<int:item_id>/',views.request_return_order_item,name='request_return_order_item'),
    path('payment-confirmation/', views.payment_confirmation, name='payment_confirmation'),

    path('wishlist_view/',views.wishlist_view,name='wishlistview'),
    path("add_to_wishlist/<int:product_id>/",views.add_to_wishlist,name='add_to_wishlist'),
    path("remove_item_wishlist/<int:wihslist_id>",views.remove_item_wishlist,name="remove_item_wishlist"),

    path('payment_success/', views.payment_success, name="payment_success"),
    path('payment_failure/',views.order_failure,name="payment_failure"),
    path('invoice/<int:order_id>/',views.invoice,name='invoice')

]