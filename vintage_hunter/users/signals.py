from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import InstrumentFinderResult
from .tasks import publish_delayed_user_message


@receiver(user_logged_in)
def on_user_login(sender, user, request, **kwargs):
    results = InstrumentFinderResult.objects.filter(is_viewed=False, finder__user=user).all()
    if results.count() > 0:
        publish_delayed_user_message.apply_async(args=[user.id, _('You have new, unviewed instruments search results.'), 'success'], countdown=5)
