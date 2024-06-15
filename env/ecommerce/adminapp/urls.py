from django.urls import path
from . import views

urlpatterns = [
    path("adminlog/", views.adminlog, name="adminlog"),
    path("dashboard/", views.dash_view, name="dashboard"),

    path("greet_based_on_time/", views.greet_based_on_time, name="greet_based_on_time"),

    path("customer/", views.customer_view, name="customer"),
    path("user_block/<int:user_id>/", views.user_block, name="user_block"),
    path("user_unblock/<int:user_id>/", views.user_unblock, name="user_unblock"),

    path("category/", views.category_view, name="category"),
    path("addcatergory/", views.add_category, name="addcategory"),
    path("delete/<int:category_id>/", views.sf_delete_cat, name="delete"),
    path("restore_cat/<int:category_id>/", views.restore_cat, name="restore_cat"),
    path("edit_category/<int:category_id>/", views.edit_category, name="edit_category"),
    path("list_category/<int:category_id>/", views.list_category, name="list_category"),
    path("unlist_category/<int:category_id>/",views.unlist_category,name="unlist_category"),
    path("trash/", views.trash, name="trash"),
    path("trash_remove/<int:category_id>/", views.trash_remove, name="trash_remove"),
    path("logout/", views.log_out, name="logout"),
    path('order_view/',views.order_view,name='order_view'),
    path('ordered_item/<int:order_id>/',views.ordered_item,name='ordered_item'),
    path('update_order_status/<int:order_id>',views.update_order_status,name='update_order_status'),
    path('confirm_return_order_item/<int:item_id>/',views.confirm_return_order_item,name='confirm_return_order_item'),
    path('view_coupon/',views.view_coupon,name="view_coupon"),
    path('add_coupon/',views.add_coupon,name='add_coupon'),
    path('edit_coupon/<int:coupon_id>/',views.edit_coupon,name='edit_coupon'),
    path('delete_coupon/<int:coupon_id>/',views.del_coupon,name='delete_coupon'),
]
