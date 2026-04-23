from decimal import Decimal
from functools import cached_property

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

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
    STATUS_LABELS = {
        'draft': _('Draft'),
        'scheduled': _('Scheduled'),
        'active': _('Active'),
        'ended': _('Ended'),
        'cancelled': _('Cancelled'),
    }

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    began_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    
    participants = models.ManyToManyField(User, related_name='registered_auctions', blank=True)
    min_participants = models.PositiveIntegerField(default=0)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    bid_interval = models.PositiveIntegerField(default=60, help_text='Timeout between bids in seconds')

    @cached_property
    def participants_count(self):
        return self.participants.distinct().count()

    @property
    def is_full(self):
        if self.max_participants is None:
            return False
        return self.participants_count >= self.max_participants

    @property
    def is_registration_available(self):
        if self.status == 'scheduled' and not self.registration_deadline:
            return True
        
        from django.utils import timezone
        return self.status == 'scheduled' and timezone.now() < self.registration_deadline
    
    @property
    def has_begun(self):
        return self.status in ['active', 'ended', 'cancelled']

    def __str__(self):
        return self.title

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @transaction.atomic
    def activate(self):
        """Activates the auction and all its waiting lots."""
        if self.status != 'scheduled':
            return False
            
        self.status = 'active'
        self.save(update_fields=['status', 'updated_at'])
        
        for lot in self.lots.filter(status='waiting'):
            lot.activate()
            
        return True

    @transaction.atomic
    def cancel(self):
        """Cancels the auction and withdraws all its lots."""
        if self.status in ['ended', 'cancelled']:
            return False

        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])
        
        for lot in self.lots.filter(status__in=['waiting', 'active']):
            lot.withdraw()
            
        return True

def get_user_active_auctions_count(self):
    if not self.is_authenticated:
        return 0
    
    return self.registered_auctions.filter(status='active').distinct().count()

active_auctions_count_property = cached_property(get_user_active_auctions_count)
User.add_to_class('active_auctions_count', active_auctions_count_property)
active_auctions_count_property.__set_name__(User, 'active_auctions_count')

class Lot(Base):
    LOT_STATUS = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('payment_pending', 'Payment Pending'),
        ('sold', 'Sold'),
        ('withdrawn', 'Withdrawn'),
    ]

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='lots')
    instrument = models.OneToOneField(Instrument, on_delete=models.PROTECT, related_name='auction_lot')
    
    lot_number = models.PositiveIntegerField(db_index=True)
    status = models.CharField(max_length=20, choices=LOT_STATUS, default='waiting')
    expires_at = models.DateTimeField(null=True, blank=True)
    payment_expires_at = models.DateTimeField(null=True, blank=True)

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

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            self.instrument.is_auction = True
            self.instrument.save(update_fields=['is_auction'])
        
        if self.status == 'sold':
            self.instrument.is_sold = True
            self.instrument.is_auction = False
            self.instrument.save(update_fields=['is_sold', 'is_auction'])
        elif self.status in ['waiting', 'active']:
            if not self.instrument.is_auction:
                self.instrument.is_auction = True
                self.instrument.save(update_fields=['is_auction'])
        else:
            if self.instrument.is_auction:
                self.instrument.is_auction = False
                self.instrument.save(update_fields=['is_auction'])

    @transaction.atomic
    def delete(self, *args, **kwargs):
        self.instrument.is_auction = False
        self.instrument.save(update_fields=['is_auction'])
        super().delete(*args, **kwargs)

    @property
    def current_highest_bid(self):
        return self.bets.filter(is_valid=True).order_by('-amount').first()

    def activate(self):
        """Sets lot status to active. Timing is handled on first bid."""
        if self.status == 'waiting':
            self.status = 'active'
            self.expires_at = None
            self.save(update_fields=['status', 'expires_at', 'updated_at'])
            return True
        return False

    def withdraw(self):
        """Withdraws the lot."""
        if self.status in ['waiting', 'active']:
            self.status = 'withdrawn'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

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
