from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("add_cart/", views.add_cart, name="add_cart"),
    path("update_quantity/", views.update_tot_price, name="update_quantity"),
    path("remove_cart/<int:cart_id>/", views.remove_cart, name="remove_cart"),
    path('checkout/',views.checkout,name='checkout')

]
