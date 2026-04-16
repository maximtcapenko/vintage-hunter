from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Collection

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        labels = {
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'email': _('Email address'),
            'username': _('Username'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last name')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            raise ValidationError(_('This email is already in use.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            raise ValidationError(_('This username is already taken.'))
        return username

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description', 'is_default']
        labels = {
            'name': _('Name'),
            'description': _('Description'),
            'is_default': _('Set as primary collection'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Collection name (for example, My Favorites)')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Optional description...')}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
