from django.urls import path
from . import views

urlpatterns = [

    path("product/", views.view_product, name="product"),
    path("addproduct/", views.add_product, name="addproduct"),
    path("addvariant/<int:product_id>/", views.add_variant, name="addvariant"),
    path("delete_prod/<int:product_id>/", views.delete_prod, name="delete_prod"),
    path("list_prod/<int:product_id>/", views.list_prod, name="list_prod"),
    path("unlist_prod/<int:product_id>/", views.unlist_prod, name="unlist_prod"),
    path("edit_prod/<int:product_id>/", views.edit_prod, name="edit_prod"),
    path("show_variants<int:product_id>/", views.showvariants, name="show_variants"),
    path('active/<int:variant_id>/', views.active, name='active'),
    path('deactivate/<int:variant_id>/', views.deactivate, name='deactivate'),
    path("editsize/<int:color_id>/", views.edit_size, name="editsize"),
    path("editvariant/<int:product_id>/",views.edit_variant,name='editvariant'),
    path('valid_color/',views.valid_color,name='valid_color'),
    path("delvariant/<int:variant_id>/",views.del_variant,name='delvariant'),
    path("search_results/", views.search_results,name="search_results"),
    path("logout/", views.log_out, name="logout"),

]
