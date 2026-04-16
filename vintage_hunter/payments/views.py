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


@login_required
@user_passes_test(is_not_staff)
def initiate_purchase(request, instrument_id):
    instrument = get_object_or_404(Instrument, pk=instrument_id, is_sold=False, is_auction=False)
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    instrument = Instrument.objects.select_for_update().get(pk=instrument_id)
                    if instrument.is_sold:
                        messages.error(request, _("Sorry, this instrument has already been sold."))
                        return redirect('catalog:get_details', id=instrument.id)

                    order = Order.objects.create(
                        user=request.user,
                        instrument=instrument,
                        amount=instrument.price,
                        status='pending'
                    )

                    provider = PaymentFactory.get_provider()
                    payment_result = provider.process_payment(
                        amount=float(instrument.price),
                        currency='USD',
                        payment_details=form.cleaned_data
                    )

                    if payment_result['status'] == 'success':
                        order.status = 'completed'
                        order.transaction_id = payment_result['transaction_id']
                        order.save()

                        instrument.is_sold = True
                        instrument.save()

                        return redirect('payments:payment_success', order_id=order.id)
                    else:
                        order.status = 'failed'
                        order.save()
                        return render(request, 'failed.html', {
                            'instrument': instrument,
                            'message': payment_result.get('message', _("Payment failed."))
                        })
            except Exception as e:
                messages.error(request, _("An error occurred during transaction: ") + str(e))
                return redirect('catalog:get_details', id=instrument.id)
    else:
        form = PurchaseForm()

    return render(request, 'purchase_form.html', {
        'form': form,
        'instrument': instrument
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
