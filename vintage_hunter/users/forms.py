from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from commons.widgets import ImagePreviewWidget
from .models import Collection, InstrumentFinder

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

class InstrumentFinderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = InstrumentFinder
        fields = [
            'name', 'brand', 'category', 'availability', 
            'vector_text_prompt', 'vector_image_prompt', 
            'frequency_minutes', 'max_results', 'is_active'
        ]
        labels = {
            'name': _('Configuration Name'),
            'brand': _('Brand'),
            'category': _('Category'),
            'availability': _('Availability'),
            'vector_text_prompt': _('Text Search Prompt'),
            'vector_image_prompt': _('Image Search Prompt'),
            'frequency_minutes': _('Search Frequency (minutes)'),
            'max_results': _('Maximum Results'),
            'is_active': _('Active'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g. Vintage Gibsons')}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'vector_text_prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Describe what you are looking for...')}),
            'vector_image_prompt': ImagePreviewWidget(attrs={'class': 'form-control'}),
            'frequency_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 10}),
            'max_results': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


    def save(self, commit = ...):
        self.instance.user = self.user
        return super().save(commit)
        
    def clean(self):
        cleaned_data = super().clean()
        frequency_minutes = cleaned_data.get('frequency_minutes')
        max_results = cleaned_data.get('max_results')

        if frequency_minutes is not None and frequency_minutes < 10:
            self.add_error('frequency_minutes', _('Minimum frequency is 10 minutes.'))
        
        if max_results is not None and max_results > 10:
            self.add_error('max_results', _('Maximum results is 10.'))
        
        if self.user and self.instance._state.adding:
            count = InstrumentFinder.objects.filter(user=self.user).count()
            if count >= 5:
                raise ValidationError(_('You can only have up to 5 finder configurations.'))
        
        return cleaned_data
