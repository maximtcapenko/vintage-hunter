from django import forms
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

from commons.mixins import SearchFormMixin
from .models import Auction, Lot
from catalog.models import Instrument


class SearchAuctionForm(forms.Form, SearchFormMixin):
    participant = forms.ModelChoiceField(User.objects.all(), required=False)
    status = forms.ChoiceField(choices=Auction.STATUS_CHOICES, required=False)
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SearchFormMixin.__init__(self)

        self.__resolvers__ = {
            'participant': lambda field: None if user.id != field.id else models.Q(participants__in=[field]),
            'status': lambda field: models.Q(status__in=[field])
        }

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'description', 'status', 'began_at', 'ended_at']
        widgets = {
            'began_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ended_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = [
            'lot_number', 'starting_price', 'reserve_price', 
            'estimated_price_min', 'estimated_price_max'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class InstrumentSearchForm(forms.Form):
    q = forms.CharField(
        required=False, 
        label='Search Instruments',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by title, brand, or year...'})
    )
