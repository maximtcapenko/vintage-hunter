from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from commons.sse import broadcast_event

from .models import Auction, Bid, Lot

@receiver(post_save, sender=Bid)
def broadcast_new_bid(sender, instance, created, **kwargs):
    if created and instance.is_valid:
        broadcast_event(
            f'auction:{instance.lot.auction.id}',
            'new_bid',
            {
                'lot_id': str(instance.lot.id),
                'amount': float(instance.amount),
                'bidder': instance.participant.username
            }
        )


@receiver(post_save, sender=Lot)
def broadcast_lot_status_update(sender, instance, created, **kwargs):
    if not created:
        broadcast_event(
            f'auction:{instance.auction.id}',
            'status_update',
            {
                'lot_id': str(instance.id),
                'status': instance.status
            }
        )


@receiver(m2m_changed, sender=Auction.participants.through)
def broadcast_auction_participant_joined(sender, instance, action, pk_set, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        broadcast_event(
            f'auction:{instance.id}',
            'participant_update',
            {
                'auction_id': str(instance.id),
                'participants_count': instance.participants_count
            }
        )
