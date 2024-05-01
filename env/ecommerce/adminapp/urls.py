from django.urls import path
from . import views

urlpatterns = [

    path('adminlog/',views.adminlog,name='adminlog'),

    path('dashboard/',views.dash_view,name='dashboard'),
    path('greet_based_on_time/',views.greet_based_on_time,name='greet_based_on_time'),

    path('customer/',views.customer_view,name='customer'),
    path('user_block/<int:user_id>/',views.user_block,name='user_block'),
    path('user_unblock/<int:user_id>/',views.user_unblock,name='user_unblock'),

    path('category/',views.category_view,name='category'),
    path('addcatergory/',views.add_category,name='addcategory'),    
    path('delete/<int:category_id>/', views.sf_delete_cat, name='delete'),
    path('restore_cat/<int:category_id>/',views.restore_cat,name='restore_cat'),
    path('edit_category/<int:category_id>/',views.edit_category,name='edit_category'),
    path('list_category/<int:category_id>/',views.list_category,name='list_category'),
    path('unlist_category/<int:category_id>/',views.unlist_category,name='unlist_category'),
    path('trash/',views.trash,name='trash'),
    path('trash_remove/<int:category_id>/',views.trash_remove,name='trash_remove'),
    
    path('logout/',views.log_out,name='logout'),
]