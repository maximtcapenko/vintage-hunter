from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from catalog.models import Brand, Category, Instrument
from commons.functional import add_to_class
from commons.models import Base


class Collection(Base):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    instruments = models.ManyToManyField(Instrument, related_name='in_collections', blank=True)

    class Meta(Base.Meta):
        unique_together = ('user', 'name')
        verbose_name = 'Collection'
        verbose_name_plural = 'Collections'

    def __str__(self):
        return f"{self.user.username}'s {self.name}"

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
    
    frequency_minutes = models.PositiveIntegerField(default=60)
    max_results = models.PositiveIntegerField(default=10)
    
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.name} ({self.user.username})"

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
