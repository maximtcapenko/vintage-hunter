from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from auction.models import Auction, Lot
from commons.sse import broadcast_event
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_lot_timeouts():
    now = timezone.now()
    
    expired_active_lots = Lot.objects.filter(status='active', expires_at__lte=now)
    for lot in expired_active_lots:
        if lot.current_highest_bid:
            lot.status = 'payment_pending'
            lot.winner = lot.current_highest_bid.participant
            lot.winning_bid = lot.current_highest_bid
            lot.final_price = lot.current_highest_bid.amount
            lot.payment_expires_at = now + timedelta(minutes=settings.PURCHASE_RESERVATION_MINUTES)
            lot.save()
            broadcast_event(
                f'auction:{lot.auction.id}', 
                'lot_payment_pending', { 
                    'lot_id': f'{lot.id}',
                    'winner_username': lot.winner.username,
                    'instrument_id': f'{lot.instrument.id}',
                    'payment_expires_at': lot.payment_expires_at.isoformat() if lot.payment_expires_at else None
            })
        else:
            lot.status = 'withdrawn'
            lot.save()
            broadcast_event(
                f'auction:{lot.auction.id}',
                'lot_payment_withdrawn', {'lot_id': f'{lot.id}'}
            )

    pending_lots = Lot.objects.filter(status='payment_pending', payment_expires_at__lte=now)
    for lot in pending_lots:
        lot.status = 'withdrawn'
        lot.winner = None
        lot.winning_bid = None
        lot.final_price = None
        lot.payment_expires_at = None
        lot.save()

@shared_task
def start_scheduled_auctions():
    now = timezone.now()
    scheduled_auctions = Auction.objects.filter(status='scheduled', began_at__lte=now)
    
    for auction in scheduled_auctions:
        with transaction.atomic():
            auction = Auction.objects.select_for_update().get(pk=auction.pk)
            if auction.status != 'scheduled':
                continue
            
            participants_count = auction.participants.count()
                
            if participants_count >= auction.min_participants:
                if auction.activate():
                    broadcast_event(
                        f'auction:{auction.id}',
                        'auction_started',
                        {'auction_id': f'{auction.id}'}
                    )
            else:
                if auction.cancel():
                    broadcast_event(
                        f'auction:{auction.id}',
                        'auction_cancelled',
                        {'auction_id': f'{auction.id}'}
                    )

@shared_task
def check_auction_reminders():
    now = timezone.now()
    auctions = Auction.objects.filter(
        status='scheduled',
        remind_sent=False,
        remind_before_start__isnull=False,
        began_at__isnull=False
    )
    
    for auction in auctions:
        reminder_time = auction.began_at - timedelta(minutes=auction.remind_before_start)
        if now >= reminder_time:
            send_auction_reminder.delay(auction.id)

@shared_task
def send_auction_reminder(auction_id):
    updated_count = Auction.objects.filter(
        id=auction_id,
        remind_sent=False,
        status='scheduled'
    ).update(remind_sent=True)
    
    if updated_count == 1:
        auction = Auction.objects.get(id=auction_id)
        logger.info(f"Sending reminder for auction: {auction.title} (ID: {auction_id})")
        
        participants = auction.participants.all()
        
        for user in participants:
            broadcast_event(
                f'user:{user.id}',
                'auction_reminder',
                {
                    'auction_id': f'{auction_id}',
                    'title': auction.title,
                    'began_at': auction.began_at.isoformat(),
                    'message': _("Reminder: The auction '%(title)s' starts soon!") % {'title': auction.title}
                }
            )
    else:
        logger.info(f"Reminder already handled for auction ID: {auction_id}")
