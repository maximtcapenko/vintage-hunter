from django.utils.translation import gettext_lazy as _

CONDITION_CHOICES = [
    ('mint', 'Mint (Like New)'),
    ('excellent', 'Excellent'),
    ('very_good', 'Very Good'),
    ('good', 'Good (Player Grade)'),
    ('fair', 'Fair (Project)'),
]

CONDITION_LABELS = {
    'mint': _('Mint (Like New)'),
    'excellent': _('Excellent'),
    'very_good': _('Very Good'),
    'good': _('Good (Player Grade)'),
    'fair': _('Fair (Project)'),
}
