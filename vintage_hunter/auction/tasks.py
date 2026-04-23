from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from auction.models import Auction, Lot
from commons.sse import broadcast_event

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
                    'payment_expires_at': lot.payment_expires_at
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
