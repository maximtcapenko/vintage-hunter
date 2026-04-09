from django import forms

from .models import Category

class SearchForm(forms.Form):
    category = forms.ModelChoiceField(Category.objects.all())

    def get_filters(self):
        filter = {}
        if self.is_valid():
            for field in self.fields:
                value = self.cleaned_data.get(field)
                if value:
                    filter[field] = value
                    
        return filter