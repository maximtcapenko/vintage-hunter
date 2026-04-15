from django.urls import path

from . import views, views_sse

app_name = 'auction'

urlpatterns = [
    path('', views.get_list, name='get_list'),
    path('create/', views.create_auction, name='create_auction'),
    path('<uuid:id>/', views.get_details, name='get_details'),
    path('<uuid:id>/edit/', views.edit_auction, name='edit_auction'),
    path('<uuid:id>/manage/', views.manage_auction, name='manage_auction'),
    path('<uuid:id>/bids/<uuid:lot_id>', views.place_bid, name='place_bid'),
    path('<uuid:id>/participants', views.register_as_participant, name='register_as_participant'),
    
    # Lot management
    path('<uuid:id>/lots/add/select/', views.add_lot_select, name='add_lot_select'),
    path('<uuid:id>/lots/add/configure/<uuid:instrument_id>/', views.add_lot_configure, name='add_lot_configure'),
    path('<uuid:id>/lots/<uuid:lot_id>/edit/', views.edit_lot, name='edit_lot'),
    path('<uuid:id>/lots/<uuid:lot_id>/delete/', views.delete_lot, name='delete_lot'),
    path('stream/<uuid:auction_id>/', views_sse.stream_events, name='stream_events'),
]
