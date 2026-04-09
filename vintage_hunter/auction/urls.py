from django.urls import path

from . import views

app_name = 'auction'

urlpatterns = [
    path('', views.get_list, name='get_list'),
    path('<uuid:id>/', views.get_details, name='get_details'),
    path('<uuid:id>/bids/<uuid:lot_id>', views.place_bid, name='place_bid'),
    path('<uuid:id>/participants', views.register_as_participant, name='register_as_participant')
]
