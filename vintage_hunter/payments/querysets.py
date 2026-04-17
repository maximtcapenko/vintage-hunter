from django.db import models
from django.utils import timezone


class OrderQuerySet(models.QuerySet):
    def active_reservations(self):
        return self.filter(status='pending', expires_at__gt=timezone.now())

    def expired_reservations(self):
        now = timezone.now()
        return self.filter(status='pending').filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__lte=now)
        )
