from django import forms
from django.db import models
from django.contrib.auth.models import User

from commons.mixins import SearchFormMixin
from .models import Auction


class SearchAuctionForm(forms.Form, SearchFormMixin):
    participant = forms.ModelChoiceField(User.objects.all())
    status = forms.ChoiceField(choices=Auction.STATUS_CHOICES)
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SearchFormMixin.__init__(self)

        self.__resolvers__ = {
            'participant': lambda field: None if user.id != field.id else models.Q(participants__in=[field]),
            'status': lambda field: models.Q(status__in=[field])
        }
