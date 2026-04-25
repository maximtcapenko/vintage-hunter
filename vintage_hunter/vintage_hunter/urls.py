"""
URL configuration for vintage_tone project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from .views import password_reset, signin, signout, signup
from commons import views_sse as sse_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', RedirectView.as_view(pattern_name='catalog:get_list', permanent=False)),
    path('signin/', signin, name='signin'),
    path('signup/', signup, name='signup'),
    path('signout/', signout, name='signout'),
    path('password_reset/', password_reset, name='password_reset'),
    path('catalog/', include('catalog.urls')),
    path('auction/', include('auction.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('payments/', include('payments.urls')),
    path('profile/', RedirectView.as_view(pattern_name='users:profile', permanent=False), name='profile'),
    path('sse/user/', sse_views.stream_user_events, name='stream_user_events'),
]
