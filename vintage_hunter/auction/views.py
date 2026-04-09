from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.contrib import messages

from .models import Auction, Bid, Lot
from django.utils import timezone

@login_required
@require_GET
def get_list(request):
    auctions = Auction.objects.filter(
        status__in=['active', 'scheduled']
    ).exclude(
        status='ended'
    ).order_by('began_at')

    return render(request, 'auction_list.html', {
        'auctions': auctions,
        'now': timezone.now()
    })


@login_required
@require_GET
def get_details(request, id):
    auction = get_object_or_404(Auction, pk=id)
    is_user_participant = auction.participants.filter(id=request.user.id).exists()
    return render(request, 'auction_details.html', {
        'auction': auction,
        'is_user_participant': is_user_participant,
        'lots': auction.lots.all(),
    })



@login_required
@require_POST
@transaction.atomic
def place_bid(request, id, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id, auction__id=id)
    
    if not lot.auction.participants.filter(id=request.user.id).exists():
        messages.error(request, "You must register for this auction to bid.")
        return redirect('auction:get_details', id=lot.auction.id)

    if lot.auction.status != 'active':
        messages.error(request, "Bidding is not currently open.")
        return redirect('auction:get_details', id=lot.auction.id)

    amount_str = request.POST.get('amount')
    try:
        amount = Decimal(amount_str)
        current_highest = lot.current_highest_bid
        # Use a consistent increment (e.g., $50)
        min_bid = (current_highest.amount + 50) if current_highest else lot.starting_price
        
        if amount < min_bid:
            messages.error(request, f"Bid too low. Minimum is ${min_bid}")
        else:
            Bid.objects.create(
                participant=request.user,
                lot=lot,
                amount=amount
            )
            messages.success(request, f"Bid of ${amount} placed!")

    except (ValueError, Decimal.InvalidOperation):
        messages.error(request, "Invalid bid amount.")

    return redirect('auction:get_details', pk=lot.auction.id)

@login_required
@require_POST
def register_as_participant(request, id):
    auction = get_object_or_404(Auction, pk=id)
    auction.participants.add(request.user)
    messages.success(request, f'You are registered')
    return redirect('auction:get_details', id=auction.id)