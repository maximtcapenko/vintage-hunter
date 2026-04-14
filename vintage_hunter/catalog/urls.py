from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.get_list, name='get_list'),
    path('create/', views.create_instrument, name='create_instrument'),
    path('<uuid:id>/', views.get_details, name='get_details'),
    path('<uuid:id>/edit/', views.edit_instrument, name='edit_instrument'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<uuid:id>/edit/', views.edit_category, name='edit_category'),
    
    # Brand Management
    path('brands/', views.brand_list, name='brand_list'),
    path('brands/create/', views.create_brand, name='create_brand'),
    path('brands/<uuid:id>/edit/', views.edit_brand, name='edit_brand'),
    
    # AJAX Image Management
    path('images/upload/<uuid:instrument_id>/', views.upload_instrument_image, name='upload_instrument_image'),
    path('images/set-primary/<uuid:image_id>/', views.set_primary_image, name='set_primary_image'),
    path('images/delete/<uuid:image_id>/', views.delete_instrument_image, name='delete_instrument_image'),
]
