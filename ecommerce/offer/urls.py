from django.urls import path
from. import views

urlpatterns = [
    path("view_offer/",views.view_offers,name="view_offer"),
    path("add_offer/",views.add_offer,name='add_offer'),
    path("edit_offer/<int:offer_id>/",views.edit_offer,name="edit_offer"),
    path("active_offer/<int:id>/",views.active_offers,name="active_offer")
    
]