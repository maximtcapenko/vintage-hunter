from django.contrib import admin

from .models import Category, Instrument, Brand, InstrumentImage


admin.site.register(Category)
admin.site.register(Instrument)
admin.site.register(Brand)
admin.site.register(InstrumentImage)
