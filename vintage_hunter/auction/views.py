from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from catalog.models import Instrument
from commons.functional import is_not_staff, is_staff, DEFAULT_PAGE_SIZE
from commons.sse import broadcast_event

from .forms import AuctionForm, InstrumentSearchForm, LotForm, SearchAuctionForm
from .models import Auction, Bid, Lot


@login_required
@require_GET
def get_list(request):
    form = SearchAuctionForm(request.user, request.GET)
    
    auctions = Auction.objects.order_by('began_at')
    if not request.user.is_staff:
        auctions = auctions.exclude(status='draft')

    paginator = Paginator(form.get_search_queryset(auctions), DEFAULT_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'auction_list.html', {
        'page': page,
        'total_count': paginator.count,
        'now': timezone.now()
    })

@login_required
@require_GET
def get_details(request, id):
    auction = get_object_or_404(Auction, pk=id)
    if not request.user.is_staff and auction.status == 'draft':
        raise Http404(_('Auction not found.'))
    
    is_user_participant = auction.participants.filter(id=request.user.id).exists()
    return render(request, 'auction_details.html', {
        'auction': auction,
        'is_user_participant': is_user_participant,
        'lots': auction.lots.exclude(status__in=('sold','withdrawn')).all(),
    })

@login_required
@user_passes_test(is_not_staff)
@require_POST
@transaction.atomic
def place_bid(request, id, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id, auction__id=id)
    if lot.instrument.is_draft:
        messages.error(request, _('This instrument is under review and bidding is temporarily locked.'))
        return redirect('auction:get_details', id=lot.auction.id)

    if not lot.auction.participants.filter(id=request.user.id).exists():
        messages.error(request, _('You must register for this auction to bid.'))
        return redirect('auction:get_details', id=lot.auction.id)

    if lot.status != 'active':
        messages.error(request, _('Bidding is not currently open.'))
        return redirect('auction:get_details', id=lot.auction.id)
    
    if lot.expires_at and timezone.now() > lot.expires_at:
        messages.error(request, _('Bidding is closed.'))
        return redirect('auction:get_details', id=lot.auction.id)

    amount_str = request.POST.get('amount')
    try:
        amount = Decimal(amount_str)
        current_highest = lot.current_highest_bid
        min_bid = (current_highest.amount + 50) if current_highest else lot.starting_price
        
        if amount < min_bid:
            messages.error(
                request,
                _('Bid too low. Minimum is $%(amount)s') % {'amount': min_bid}
            )
        else:
            bid = Bid.objects.create(
                participant=request.user,
                lot=lot,
                amount=amount
            )
            
            lot.expires_at = timezone.now() + timezone.timedelta(seconds=lot.auction.bid_interval)
            lot.save(update_fields=['expires_at'])
            
            broadcast_event(
            f'auction:{lot.auction.id}',
            'new_bid',
            {
                'lot_id': f'{lot.id}',
                'amount': float(bid.amount),
                'bidder': request.user.username,
                'expires_at': lot.expires_at.isoformat() if lot.expires_at else None
            })

            messages.success(
                request,
                _('Bid of $%(amount)s placed!') % {'amount': amount}
            )

    except (ValueError, Decimal.InvalidOperation):
        messages.error(request, _('Invalid bid amount.'))

    return redirect('auction:get_details', id=lot.auction.id)

@login_required
@user_passes_test(is_not_staff)
@require_POST
def register_as_participant(request, id):
    auction = get_object_or_404(Auction, pk=id)

    if auction.status != 'scheduled':
        messages.error(request, _('Registration is only available for scheduled auctions.'))
        return redirect('auction:get_details', id=auction.id)

    if not auction.is_registration_available:
        messages.error(request, _('Registration deadline has passed.'))
        return redirect('auction:get_details', id=auction.id)

    if auction.is_full:
        messages.error(request, _('This auction has reached the maximum number of participants.'))
        return redirect('auction:get_details', id=auction.id)

    auction.participants.add(request.user)
    messages.success(request, _('You are registered as a participant.'))

    return redirect('auction:get_details', id=auction.id)

@login_required
@user_passes_test(is_staff)
@require_http_methods(['GET', 'POST'])
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save()
            messages.success(
                request,
                _('Auction "%(auction)s" created successfully.') % {'auction': auction.title}
            )
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = AuctionForm(initial={
            'status': 'draft',
            'min_participants': settings.AUCTION_DEFAULT_MIN_PARTICIPANTS
            })
    
    return render(request, 'auction_form.html', {'form': form, 'title': _('Create New Auction')})

@login_required
@user_passes_test(is_staff)
@require_http_methods(['GET', 'POST'])
def edit_auction(request, id):
    auction = get_object_or_404(Auction, pk=id)
    if request.method == 'POST':
        form = AuctionForm(request.POST, instance=auction)
        if form.is_valid():
            auction = form.save()
            messages.success(
                request,
                _('Auction "%(auction)s" updated.') % {'auction': auction.title}
            )
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = AuctionForm(instance=auction)
    
    return render(
        request,
        'auction_form.html',
        {'form': form, 'title': _('Edit Auction: %(auction)s') % {'auction': auction.title}}
    )

@login_required
@user_passes_test(is_staff)
@require_GET
def manage_auction(request, id):
    auction = get_object_or_404(Auction, pk=id)
    lots = auction.lots.all().order_by('lot_number')

    total_low_estimate = lots.aggregate(models.Sum('estimated_price_min'))['estimated_price_min__sum'] or 0
    
    return render(request, 'auction_manage.html', {
        'auction': auction,
        'lots': lots,
        'total_low_estimate': total_low_estimate,
    })

@login_required
@user_passes_test(is_staff)
@require_GET
def add_lot_select(request, id):
    auction = get_object_or_404(Auction, pk=id)
    if auction.has_begun:
        messages.error(request, _('Cannot add lots after auction has begun.'))
        return redirect('auction:manage_auction', id=auction.id)

    search_form = InstrumentSearchForm(request.GET)
    
    instruments = Instrument.objects.filter(
        is_auction=False,
        auction_lot__isnull=True,
        is_sold=False,
        is_draft=False
    )
    
    if search_form.is_valid() and search_form.cleaned_data.get('q'):
        q = search_form.cleaned_data['q']
        instruments = instruments.filter(
            Q(title__icontains=q) | 
            Q(brand__name__icontains=q) |
            Q(year__icontains=q)
        )
    
    paginator = Paginator(instruments, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'lot_add_select.html', {
        'auction': auction,
        'page_obj': page_obj,
        'search_form': search_form,
    })

@login_required
@user_passes_test(is_staff)
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def add_lot_configure(request, id, instrument_id):
    auction = get_object_or_404(Auction, pk=id)
    if auction.has_begun:
        messages.error(request, _('Cannot add lots after auction has begun.'))
        return redirect('auction:manage_auction', id=auction.id)

    instrument = get_object_or_404(
        Instrument,
        pk=instrument_id,
        is_auction=False,
        auction_lot__isnull=True,
        is_draft=False
    )
    
    if request.method == 'POST':
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.auction = auction
            lot.instrument = instrument
            lot.save()
            
            messages.success(
                request,
                _('Lot added: %(instrument)s') % {'instrument': instrument}
            )
            return redirect('auction:manage_auction', id=auction.id)
    else:
        max_lot = auction.lots.aggregate(models.Max('lot_number'))['lot_number__max'] or 0
        form = LotForm(initial={
            'lot_number': max_lot + 1,
            'starting_price': instrument.price,
            'estimated_price_min': instrument.price * Decimal('0.9'),
            'estimated_price_max': instrument.price * Decimal('1.2'),
        })
    
    return render(request, 'lot_form.html', {
        'form': form,
        'auction': auction,
        'instrument': instrument,
        'title': _('Configure Lot Details')
    })

@login_required
@user_passes_test(is_staff)
@require_http_methods(['GET', 'POST'])
def edit_lot(request, id, lot_id):
    auction = get_object_or_404(Auction, pk=id)
    if auction.has_begun:
        messages.error(request, _('Cannot edit lots after auction has begun.'))
        return redirect('auction:manage_auction', id=auction.id)

    lot = get_object_or_404(Lot, pk=lot_id, auction=auction)
    
    if request.method == 'POST':
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Lot %(lot_number)s updated.') % {'lot_number': lot.lot_number}
            )
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = LotForm(instance=lot)
    
    return render(request, 'lot_form.html', {
        'form': form,
        'auction': auction,
        'instrument': lot.instrument,
        'title': _('Edit Lot %(lot_number)s') % {'lot_number': lot.lot_number}
    })

@login_required
@user_passes_test(is_staff)
@require_POST
@transaction.atomic
def delete_lot(request, id, lot_id):
    auction = get_object_or_404(Auction, pk=id)
    if auction.has_begun:
        messages.error(request, _('Cannot delete lots after auction has begun.'))
        return redirect('auction:manage_auction', id=auction.id)

    lot = get_object_or_404(Lot, pk=lot_id, auction=auction)
    
    lot.delete()
    messages.success(request, _('Lot removed from auction.'))
    return redirect('auction:manage_auction', id=auction.id)
