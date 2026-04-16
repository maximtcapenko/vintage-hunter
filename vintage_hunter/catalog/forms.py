from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from commons.mixins import SearchFormMixin
from .models import Brand, Category, Instrument, InstrumentImage
from .widgets import SpecificationsWidget


class SearchCatalogForm(forms.Form, SearchFormMixin):
    category = forms.ModelChoiceField(
        Category.objects.all(),
        required=False,
        label=_('Category')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SearchFormMixin.__init__(self)

        self.__resolvers__ = {
            'category': lambda field: models.Q(category=field),
        }

class InstrumentForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = [
            'title', 'category', 'brand', 'year', 'serial_number', 
            'condition', 'is_original', 'has_repairs', 'is_concert_ready',
            'price', 'description', 'specifications'
        ]
        labels = {
            'title': _('Instrument title'),
            'category': _('Category'),
            'brand': _('Brand'),
            'year': _('Year'),
            'serial_number': _('Serial number'),
            'condition': _('Condition'),
            'is_original': _('All original'),
            'has_repairs': _('Has repairs'),
            'is_concert_ready': _('Concert ready'),
            'price': _('Price'),
            'description': _('Description'),
            'specifications': _('Technical specifications'),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'specifications': SpecificationsWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['condition'].choices = [
            (value, Instrument.CONDITION_LABELS[value])
            for value, _label in Instrument.CONDITION_CHOICES
        ]
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})

class InstrumentImageForm(forms.ModelForm):
    class Meta:
        model = InstrumentImage
        fields = []

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': _('Category name'),
            'description': _('Description'),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'origin_country', 'history']
        labels = {
            'name': _('Brand name'),
            'origin_country': _('Origin country'),
            'history': _('History'),
        }
        widgets = {
            'history': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
