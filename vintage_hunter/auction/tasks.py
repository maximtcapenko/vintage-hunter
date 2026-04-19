from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from auction.models import Lot

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
        else:
            lot.status = 'withdrawn'
            lot.save()

    pending_lots = Lot.objects.filter(status='payment_pending', payment_expires_at__lte=now)
    for lot in pending_lots:
        lot.status = 'withdrawn'
        lot.winner = None
        lot.winning_bid = None
        lot.final_price = None
        lot.payment_expires_at = None
        lot.save()
