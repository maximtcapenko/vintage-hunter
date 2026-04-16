from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('purchase/<uuid:instrument_id>/', views.initiate_purchase, name='initiate_purchase'),
    path('success/<uuid:order_id>/', views.payment_success, name='payment_success'),
    path('failed/', views.payment_failed, name='payment_failed'),
]
