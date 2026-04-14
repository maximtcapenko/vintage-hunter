from decimal import Decimal

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction, models
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render, Http404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.db.models import Q

from .models import Auction, Bid, Lot
from .forms import SearchAuctionForm, AuctionForm, LotForm, InstrumentSearchForm
from catalog.models import Instrument


DEFAULT_PAGE_SIZE = 50

def is_staff(user):
    return user.is_authenticated and user.is_staff

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
        raise Http404("Auction not found.")
    
    is_user_participant = auction.participants.filter(id=request.user.id).exists()
    return render(request, 'auction_details.html', {
        'auction': auction,
        'is_user_participant': is_user_participant,
        'lots': auction.lots.exclude(status__in=('sold','withdrawn')).all(),
    })

@login_required
@require_POST
@transaction.atomic
def place_bid(request, id, lot_id):
    lot = get_object_or_404(Lot, pk=lot_id, auction__id=id)
    
    if not lot.auction.participants.filter(id=request.user.id).exists():
        messages.error(request, 'You must register for this auction to bid.')
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
            messages.error(request, f'Bid too low. Minimum is ${min_bid}')
        else:
            Bid.objects.create(
                participant=request.user,
                lot=lot,
                amount=amount
            )
            messages.success(request, f'Bid of ${amount} placed!')

    except (ValueError, Decimal.InvalidOperation):
        messages.error(request, 'Invalid bid amount.')

    return redirect('auction:get_details', id=lot.auction.id)

@login_required
@require_POST
def register_as_participant(request, id):
    auction = get_object_or_404(Auction, pk=id)
    
    if request.user.is_staff:
        messages.error(request, "Staff members cannot participate in auctions.")
        return redirect('auction:get_details', id=auction.id)

    if auction.status != 'active':
        messages.error(request, "Registration is only available for active auctions.")
        return redirect('auction:get_details', id=auction.id)

    auction.participants.add(request.user)
    messages.success(request, f'You are registered as participant.')

    return redirect('auction:get_details', id=auction.id)

# Staff Management Views

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def create_auction(request):
    if request.method == "POST":
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save()
            messages.success(request, f'Auction "{auction.title}" created successfully.')
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = AuctionForm(initial={'status': 'draft'})
    
    return render(request, 'auction_form.html', {'form': form, 'title': 'Create New Auction'})

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def edit_auction(request, id):
    auction = get_object_or_404(Auction, pk=id)
    if request.method == "POST":
        form = AuctionForm(request.POST, instance=auction)
        if form.is_valid():
            auction = form.save()
            messages.success(request, f'Auction "{auction.title}" updated.')
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = AuctionForm(instance=auction)
    
    return render(request, 'auction_form.html', {'form': form, 'title': f'Edit Auction: {auction.title}'})

@user_passes_test(is_staff)
@require_GET
def manage_auction(request, id):
    auction = get_object_or_404(Auction, pk=id)
    lots = auction.lots.all().order_by('lot_number')
    
    # Calculate some summary stats
    total_low_estimate = lots.aggregate(models.Sum('estimated_price_min'))['estimated_price_min__sum'] or 0
    
    return render(request, 'auction_manage.html', {
        'auction': auction,
        'lots': lots,
        'total_low_estimate': total_low_estimate,
    })

@user_passes_test(is_staff)
@require_GET
def add_lot_select(request, id):
    auction = get_object_or_404(Auction, pk=id)
    search_form = InstrumentSearchForm(request.GET)
    
    # Filter instruments not in auction and not already assigned as a lot
    instruments = Instrument.objects.filter(is_auction=False, auction_lot__isnull=True)
    
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

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def add_lot_configure(request, id, instrument_id):
    auction = get_object_or_404(Auction, pk=id)
    instrument = get_object_or_404(Instrument, pk=instrument_id, is_auction=False, auction_lot__isnull=True)
    
    if request.method == "POST":
        form = LotForm(request.POST)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.auction = auction
            lot.instrument = instrument
            lot.save()
            
            # Mark instrument as being in an auction
            instrument.is_auction = True
            instrument.save()
            
            messages.success(request, f'Lot added: {instrument}')
            return redirect('auction:manage_auction', id=auction.id)
    else:
        # Default lot number: max + 1
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
        'title': 'Configure Lot Details'
    })

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def edit_lot(request, id, lot_id):
    auction = get_object_or_404(Auction, pk=id)
    lot = get_object_or_404(Lot, pk=lot_id, auction=auction)
    
    if request.method == "POST":
        form = LotForm(request.POST, instance=lot)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lot {lot.lot_number} updated.')
            return redirect('auction:manage_auction', id=auction.id)
    else:
        form = LotForm(instance=lot)
    
    return render(request, 'lot_form.html', {
        'form': form,
        'auction': auction,
        'instrument': lot.instrument,
        'title': f'Edit Lot {lot.lot_number}'
    })

@user_passes_test(is_staff)
@require_POST
@transaction.atomic
def delete_lot(request, id, lot_id):
    auction = get_object_or_404(Auction, pk=id)
    lot = get_object_or_404(Lot, pk=lot_id, auction=auction)
    
    instrument = lot.instrument
    instrument.is_auction = False
    instrument.save()
    
    lot.delete()
    messages.success(request, 'Lot removed from auction.')
    return redirect('auction:manage_auction', id=auction.id)
