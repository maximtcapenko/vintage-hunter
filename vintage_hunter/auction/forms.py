from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from commons.mixins import SearchFormMixin

from .models import Auction, Lot


class SearchAuctionForm(forms.Form, SearchFormMixin):
    participant = forms.ModelChoiceField(User.objects.all(), required=False, label=_('Participant'))
    status = forms.ChoiceField(choices=(), required=False, label=_('Status'))
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SearchFormMixin.__init__(self)
        self.fields['status'].choices = [
            (value, Auction.STATUS_LABELS[value])
            for value, _label in Auction.STATUS_CHOICES
        ]

        self.__resolvers__ = {
            'participant': lambda field: None if user.id != field.id else models.Q(participants__in=[field]),
            'status': lambda field: models.Q(status__in=[field])
        }

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = [
            'title', 'description', 'status', 'began_at', 'ended_at', 
            'registration_deadline', 'remind_before_start',
            'min_participants', 'max_participants'
        ]
        labels = {
            'title': _('Title'),
            'description': _('Description'),
            'status': _('Status'),
            'began_at': _('Starts at'),
            'ended_at': _('Ends at'),
            'registration_deadline': _('Registration deadline'),
            'remind_before_start': _('Advance notification (minutes)'),
            'min_participants': _('Min participants'),
            'max_participants': _('Max participants'),
        }
        widgets = {
            'began_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'ended_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            (value, Auction.STATUS_LABELS[value])
            for value, _label in Auction.STATUS_CHOICES
        ]
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        min_participants = cleaned_data.get('min_participants')
        max_participants = cleaned_data.get('max_participants')

        if max_participants is not None and min_participants > max_participants:
            self.add_error(
                'min_participants',
                _('Minimum participants cannot be greater than maximum participants.')
            )

        if status != 'draft':
            if self.instance.pk:
                lots_count = self.instance.lots.count()
            else:
                lots_count = 0
                
            if lots_count == 0:
                self.add_error(
                    'status',
                    _('Cannot schedule an auction without any lots. Please add at least one lot first.')
                )
        
        return cleaned_data
# ... (LotForm and InstrumentSearchForm remain the same)


class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = [
            'lot_number', 'starting_price', 'reserve_price', 
            'estimated_price_min', 'estimated_price_max'
        ]
        labels = {
            'lot_number': _('Lot number'),
            'starting_price': _('Starting price'),
            'reserve_price': _('Reserve price'),
            'estimated_price_min': _('Low estimate'),
            'estimated_price_max': _('High estimate'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class InstrumentSearchForm(forms.Form):
    q = forms.CharField(
        required=False, 
        label=_('Search instruments'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Search by title, brand, or year...')})
    )
