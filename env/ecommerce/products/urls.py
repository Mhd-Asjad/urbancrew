from django.urls import path
from . import views

urlpatterns = [

    path('product/',views.view_product,name='product'),
    path('addproduct/',views.add_product,name='addproduct'),
    path('addimg/',views.add_image,name='addimage'),
    path('addsize/',views.addsize,name='addsize'),

    path('delete_prod/<int:product_id>/',views.delete_prod,name='delete_prod'),
    path('list_prod/<int:product_id>/',views.list_prod,name='list_prod'),
    path('unlist_prod/<int:product_id>/',views.unlist_prod,name='unlist_prod'),
    path('edit_prod/<int:product_id>/',views.edit_prod,name='edit_prod'),

    path('search_results/',views.search_results,name='search_results'),

    path('logout/',views.log_out,name='logout'),


]