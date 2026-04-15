from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class SignUpForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'}),
        label=_('Password')
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'}),
        label=_('Confirm password')
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']
        labels = {
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'email': _('Email address'),
            'username': _('Username'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': _('Leo'), 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': _('Fender'), 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'leo@vintagetone.com', 'class': 'form-control'}),
            'username': forms.TextInput(attrs={'placeholder': _('vintage_enthusiast'), 'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _('Passwords do not match.'))
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class SignInForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your credentials'),
            'id': 'username'
        }),
        label=_('Username or email')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'id': 'password'
        }),
        label=_('Password')
    )
    remember = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
        'id': 'remember'
    }), label=_('Keep me signed in'))
