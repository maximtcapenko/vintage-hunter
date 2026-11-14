from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from catalog.models import Brand, Category, Instrument
from commons.choices import CONDITION_CHOICES, CONDITION_LABELS
from commons.functional import add_to_class
from commons.models import Base

from pgvector.django import VectorField


class Collection(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    instruments = models.ManyToManyField(Instrument, related_name='in_collections', blank=True)

    class Meta(Base.Meta):
        unique_together = ('user', 'name')
        verbose_name = 'Collection'

    def save(self, *args, **kwargs):
        if self.is_default:
            Collection.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class InstrumentFinder(Base):
    AVAILABILITY_CHOICES = [
        ('all', _('All')),
        ('buy_it_now', _('Buy It Now Only')),
        ('auction', _('Auction Only')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='finders')
    name = models.CharField(max_length=100)
    
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='finders')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='finders')
    
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='all')
    
    vector_text_prompt = models.TextField(blank=True)
    vector_image_prompt = models.ImageField(upload_to='finders/%Y/%m/', null=True, blank=True)
    
    query_text_embedding = VectorField(dimensions=768, null=True, blank=True)

    frequency_minutes = models.PositiveIntegerField(default=60)
    max_results = models.PositiveIntegerField(default=10)
    
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

class InstrumentFinderResult(Base):
    finder = models.ForeignKey(InstrumentFinder, on_delete=models.CASCADE, related_name='results')
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    is_viewed = models.BooleanField(default=False)

class InstrumentHuntRequest(Base):
    CONDITION_CHOICES = CONDITION_CHOICES
    CONDITION_LABELS = CONDITION_LABELS

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('on_review', 'On Review'),
        ('in_work', 'In Work'),
        ('canceled', 'Canceled'),
        ('rejected', 'Rejected'),
    ]
    STATUS_LABELS = {
        'draft': _('Draft'),
        'sent': _('Sent'),
        'on_review': _('On Review'),
        'in_work': _('In Work'),
        'canceled': _('Canceled'),
        'rejected': _('Rejected'),
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hunt_requests')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    year = models.PositiveIntegerField(null=True, blank=True)
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='hunt_requests')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='hunt_requests')
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    is_original = models.BooleanField(default=True, help_text='Should all parts be original?')
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, blank=True)

    max_price = models.DecimalField(max_digits=12, decimal_places=2, help_text='Maximum price the user is ready to pay')

    search_in_auctions = models.BooleanField(
        default=False,
        help_text='Also search auctions and agree to take part if a matching lot is found'
    )
    max_wait_days = models.PositiveIntegerField(help_text='Maximum number of days the user is ready to wait')

    platform_commission = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Flat platform commission fee (not a percentage)'
    )
    auto_charge = models.BooleanField(
        default=False,
        help_text='Automatically charge the user once a matching instrument is found and bought'
    )

    delivery_address = models.TextField()

    non_payment_resale_agreed = models.BooleanField(
        default=False,
        help_text='User agrees the store may resell the instrument if they fail to pay within the grace period'
    )
    non_payment_resale_days = models.PositiveIntegerField(
        help_text='Grace period in days before the store may resell an unpaid instrument'
    )

    is_active = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.user})'

def get_user_user_collections_count(self):
    if not self.is_authenticated:
        return 0
    
    return self.collections.count()

add_to_class(User, get_user_user_collections_count, 'collections_count')

def get_user_orders_count(self):
    if not self.is_authenticated:
        return 0
    
    return self.orders.filter(status='completed').count()

add_to_class(User, get_user_orders_count, 'orders_count')

def get_user_active_orders_count(self):
    if not self.is_authenticated:
        return 0

    return self.orders.active_reservations().count()

add_to_class(User, get_user_active_orders_count, 'active_orders_count')

def get_user_finders_count(self):
    if not self.is_authenticated:
        return 0

    return self.finders.count()

add_to_class(User, get_user_finders_count, 'finders_count')

def get_user_hunt_request_count(self):
    if not self.is_authenticated:
        return 0

    return self.hunt_requests.count()

add_to_class(User, get_user_hunt_request_count, 'request_count')
