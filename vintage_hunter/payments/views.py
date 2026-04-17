from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from catalog.models import Instrument
from commons.functional import is_not_staff

from .forms import PurchaseForm
from .models import Order
from .utils import PaymentFactory


def instrument_reserved_message():
    return _('This instrument is temporarily reserved by another buyer. Please try again shortly.')


def reservation_expired_message():
    return _('Your purchase reservation expired. Please start checkout again.')


def expire_stale_reservations(instrument):
    Order.objects.expired_reservations().filter(instrument=instrument).update(status='failed')


@login_required
@user_passes_test(is_not_staff)
def initiate_purchase(request, instrument_id):
    instrument = get_object_or_404(Instrument, pk=instrument_id)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        try:
            with transaction.atomic():
                instrument = Instrument.objects.select_for_update().get(pk=instrument_id)
                if instrument.is_sold:
                    messages.error(request, _("Sorry, this instrument has already been sold."))
                    return redirect('catalog:get_details', id=instrument.id)
                if instrument.is_auction:
                    messages.error(request, _('This instrument is no longer available for direct purchase.'))
                    return redirect('catalog:get_details', id=instrument.id)
                if instrument.is_draft:
                    messages.error(request, _('This instrument is under review and cannot be purchased right now.'))
                    return redirect('catalog:get_details', id=instrument.id)

                expire_stale_reservations(instrument)

                order = Order.objects.select_for_update().filter(
                    pk=request.POST.get('order_id'),
                    user=request.user,
                    instrument=instrument
                ).first()
                if not order:
                    messages.error(request, reservation_expired_message())
                    return redirect('payments:initiate_purchase', instrument_id=instrument.id)
                if order.status == 'completed':
                    return redirect('payments:payment_success', order_id=order.id)
                if order.status != 'pending' or not order.is_reservation_active:
                    if order.status == 'pending':
                        order.status = 'failed'
                        order.save(update_fields=['status'])
                    messages.error(request, reservation_expired_message())
                    return redirect('payments:initiate_purchase', instrument_id=instrument.id)

                if Order.objects.active_reservations().filter(instrument=instrument).exclude(
                    user=request.user,
                    pk=order.pk
                ).exists():
                    messages.error(request, instrument_reserved_message())
                    return redirect('catalog:get_details', id=instrument.id)

                if form.is_valid():
                    provider = PaymentFactory.get_provider()
                    payment_result = provider.process_payment(
                        amount=float(instrument.price),
                        currency='USD',
                        payment_details=form.cleaned_data
                    )

                    if payment_result['status'] == 'success':
                        order.status = 'completed'
                        order.transaction_id = payment_result['transaction_id']
                        order.expires_at = None
                        order.save(update_fields=['status', 'transaction_id', 'expires_at'])

                        instrument.is_sold = True
                        instrument.save()

                        return redirect('payments:payment_success', order_id=order.id)

                    order.status = 'failed'
                    order.expires_at = None
                    order.save(update_fields=['status', 'expires_at'])
                    return render(request, 'failed.html', {
                        'instrument': instrument,
                        'message': payment_result.get('message', _("Payment failed."))
                    })
        except Exception as e:
            messages.error(request, _("An error occurred during transaction: ") + str(e))
            return redirect('catalog:get_details', id=instrument.id)
    else:
        form = PurchaseForm()
        try:
            with transaction.atomic():
                instrument = Instrument.objects.select_for_update().get(pk=instrument_id)
                if instrument.is_sold:
                    messages.error(request, _("Sorry, this instrument has already been sold."))
                    return redirect('catalog:get_details', id=instrument.id)
                if instrument.is_auction:
                    messages.error(request, _('This instrument is no longer available for direct purchase.'))
                    return redirect('catalog:get_details', id=instrument.id)
                if instrument.is_draft:
                    messages.error(request, _('This instrument is under review and cannot be purchased right now.'))
                    return redirect('catalog:get_details', id=instrument.id)

                expire_stale_reservations(instrument)

                order = Order.objects.active_reservations().filter(
                    user=request.user,
                    instrument=instrument
                ).first()
                if order is None:
                    if Order.objects.active_reservations().filter(instrument=instrument).exclude(user=request.user).exists():
                        messages.error(request, instrument_reserved_message())
                        return redirect('catalog:get_details', id=instrument.id)

                    order = Order.objects.create(
                        user=request.user,
                        instrument=instrument,
                        amount=instrument.price,
                        status='pending',
                        expires_at=Order.get_reservation_expiry()
                    )
        except Exception as e:
            messages.error(request, _("An error occurred during transaction: ") + str(e))
            return redirect('catalog:get_details', id=instrument.id)

    return render(request, 'purchase_form.html', {
        'form': form,
        'instrument': instrument,
        'order': order,
        'reservation_minutes': settings.PURCHASE_RESERVATION_MINUTES,
    })

@login_required
@user_passes_test(is_not_staff)
def payment_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user, status='completed')
    return render(request, 'success.html', {'order': order})

@login_required
@user_passes_test(is_not_staff)
def payment_failed(request):
    return render(request, 'failed.html')
