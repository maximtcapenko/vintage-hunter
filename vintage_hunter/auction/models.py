from functools import cached_property

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

from catalog.models import Instrument
from commons.models import Base


class Auction(Base):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    began_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    participants = models.ManyToManyField(User, related_name='registered_auctions', blank=True)

    @cached_property
    def participant_count(self):
        return self.participants.distinct().count()
    
    def __str__(self):
        return self.title

class Lot(Base):
    LOT_STATUS = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('passed', 'Passed (Reserve not met)'),
        ('withdrawn', 'Withdrawn'),
    ]

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='lots')
    instrument = models.OneToOneField(Instrument, on_delete=models.PROTECT, related_name='auction_lot')
    
    lot_number = models.PositiveIntegerField(db_index=True)
    status = models.CharField(max_length=20, choices=LOT_STATUS, default='waiting')

    starting_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text='Minimum price to sell')
    estimated_price_min = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Low Estimate')
    estimated_price_max = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='High Estimate')
    
    final_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_lots')
    winning_bid = models.OneToOneField(
        'Bid', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='won_lot_record'
    )

    class Meta(Base.Meta):
        ordering = ['lot_number']
        unique_together = ('auction', 'lot_number')

    @property
    def current_highest_bid(self):
        return self.bets.filter(is_valid=True).order_by('-amount').first()

class Bid(Base):
    participant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bids')
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='bets')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_valid = models.BooleanField(default=True)
    is_automatic = models.BooleanField(default=False)

    class Meta(Base.Meta):
        ordering = ['-amount']

    def __str__(self):
        return f"{self.participant.username} - {self.amount}"

class BidIncrement(models.Model):
    """
    Defines how much the next bid must be based on the current price.
    Example: $0-$1000 increment is $50. $1000+ increment is $100.
    """
    range_start = models.DecimalField(max_digits=12, decimal_places=2)
    increment_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['range_start']