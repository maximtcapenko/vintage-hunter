from django import forms
from django.utils.translation import gettext_lazy as _


class PurchaseForm(forms.Form):
    card_number = forms.CharField(
        label=_('Card Number'),
        max_length=19,
        widget=forms.TextInput(attrs={'placeholder': '0000 0000 0000 0000', 'class': 'form-control'})
    )
    expiry_date = forms.CharField(
        label=_('Expiry Date'),
        max_length=5,
        widget=forms.TextInput(attrs={'placeholder': 'MM/YY', 'class': 'form-control'})
    )
    cvv = forms.CharField(
        label=_('CVV'),
        max_length=4,
        widget=forms.PasswordInput(attrs={'placeholder': '123', 'class': 'form-control'})
    )
    cardholder_name = forms.CharField(
        label=_('Cardholder Name'),
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'JOHN DOE', 'class': 'form-control'})
    )
