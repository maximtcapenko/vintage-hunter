from django import forms
from django.utils.safestring import mark_safe

import json


class SpecificationsWidget(forms.Widget):
    template_name = 'catalog/widgets/specifications_table.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Ensure value is a dictionary for the template
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


class ImagePreviewWidget(forms.ClearableFileInput):
    template_name = 'django/forms/widgets/input.html'

    def __init__(self, *args, **kwargs):
        self.accept = kwargs.pop('accept', 'image/*')
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        if 'id' not in attrs:
            attrs['id'] = f'id_{name}'
        
        attrs['accept'] = self.accept
            
        preview_id = f'preview_{attrs["id"]}'
        
        # FIX: Use forms.FileInput.render instead of super().render()
        # This removes the "Currently:" and "Change:" labels automatically
        input_html = forms.FileInput.render(self, name, value, attrs, renderer)
        existing_url = value.url if value and hasattr(value, 'url') else '#'
        display_style = 'block' if existing_url != '#' else 'none'
        
        # Added some styling to the container for a cleaner "Vantage Tone" look
        img_html = (
            f'<div class="mb-2" style="border: 1px solid #eee; border-radius: 8px; padding: 5px; width: fit-content; background: #fff;">'
            f'<img id="{preview_id}" src="{existing_url}" class="rounded" style="max-height: 200px; display: {display_style};">'
            f'</div>'
        )

        script = f"""
        <script>
            (function() {{
                const input = document.getElementById('{attrs["id"]}');
                const preview = document.getElementById('{preview_id}');
                const originalUrl = '{existing_url}';
                const accept = '{self.accept}';
                
                input.onchange = function (evt) {{
                    const [file] = this.files;
                    if (file) {{
                        preview.src = URL.createObjectURL(file);
                        preview.style.display = 'block';
                    }} else {{
                        if (originalUrl !== '#') {{
                            preview.src = originalUrl;
                            preview.style.display = 'block';
                        }} else {{
                            preview.style.display = 'none';
                        }}
                    }}
                }};
            }})();
        </script>
        """
        
        return mark_safe(f'<div class="image-preview-widget">{img_html}{input_html}</div>{script}')

