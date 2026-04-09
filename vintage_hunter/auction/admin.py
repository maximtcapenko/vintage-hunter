from django.contrib import admin

from .models import Auction, Lot


admin.site.register(Auction)
admin.site.register(Lot)
