from django import forms
from django.db import models

from commons.mixins import SearchFormMixin
from .models import Category


class SearchCatalogForm(forms.Form, SearchFormMixin):
    category = forms.ModelChoiceField(Category.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SearchFormMixin.__init__(self)

        self.__resolvers__ = {
            'category': lambda field: models.Q(category=field),
        }
