from django.urls import path

from . import views
from .views import (
    create_collection_ajax,
    delete_collection,
    get_collection_details,
    get_collection_list,
    get_instrument_collections,
    profile_details,
    toggle_collection_item,
)

app_name = 'users'

urlpatterns = [
    path('profile/', profile_details, name='profile'),
    path('collections/', get_collection_list, name='collection_list'),
    path('collections/<uuid:id>/', get_collection_details, name='collection_details'),
    path('collections/<uuid:id>/delete/', delete_collection, name='delete_collection'),
    path('collections/status/<uuid:instrument_id>/', get_instrument_collections, name='get_instrument_collections'),
    path('collections/create-ajax/', create_collection_ajax, name='create_collection_ajax'),
    path('collections/toggle/<uuid:instrument_id>/', toggle_collection_item, name='toggle_collection_item'),
    path('orders/', views.get_orders_list, name='order_list'),
    path('purchases/', views.get_purchases_list, name='purchase_list'),
    path('purchases/<uuid:id>/', views.get_purchase_details, name='purchase_details'),
    path('finders/', views.finder_list, name='finder_list'),
    path('finders/create/', views.finder_create, name='finder_create'),
    path('finders/<uuid:id>/edit/', views.finder_update, name='finder_update'),
    path('finders/<uuid:id>/delete/', views.finder_delete, name='finder_delete'),
]
