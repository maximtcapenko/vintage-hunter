from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from catalog.models import Instrument
from commons.models import Base
from .querysets import OrderQuerySet


class Order(Base):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    objects = OrderQuerySet.as_manager()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT, related_name='orders')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} - {self.instrument.title} by {self.user.username}"

    @classmethod
    def get_reservation_expiry(cls):
        return timezone.now() + timedelta(minutes=settings.PURCHASE_RESERVATION_MINUTES)

    @property
    def is_reservation_active(self):
        return self.status == 'pending' and self.expires_at is not None and self.expires_at > timezone.now()
