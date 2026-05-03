import json

from django import forms


class SpecificationsWidget(forms.Widget):
    template_name = 'catalog/widgets/specifications_table.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        specs = {}
        if value:
            if isinstance(value, str):
                try:
                    specs = json.loads(value)
                except json.JSONDecodeError:
                    specs = {}
            else:
                specs = value
        
        context['specs'] = specs
        return context

    class Media:
        js = ('catalog/js/specifications_widget.js',)
        css = {
            'all': ('catalog/css/specifications_widget.css',)
        }

