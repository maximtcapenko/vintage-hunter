from django.urls import path
from .views import (
    profile_details, 
    get_collection_list, 
    get_collection_details, 
    delete_collection,
    toggle_collection_item,
    get_instrument_collections,
    create_collection_ajax
)

app_name = 'users'

urlpatterns = [
    path('profile/', profile_details, name='profile'),
    path('collections/', get_collection_list, name='collection_list'),
    path('collections/<uuid:pk>/', get_collection_details, name='collection_details'),
    path('collections/<uuid:pk>/delete/', delete_collection, name='delete_collection'),
    path('collections/status/<uuid:instrument_id>/', get_instrument_collections, name='get_instrument_collections'),
    path('collections/create-ajax/', create_collection_ajax, name='create_collection_ajax'),
    path('collections/toggle/<uuid:instrument_id>/', toggle_collection_item, name='toggle_collection_item'),
]
