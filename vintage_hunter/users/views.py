import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from catalog.models import Instrument
from commons.functional import is_not_staff
from payments.models import Order

from .forms import CollectionForm, UserProfileForm
from .models import Collection


@login_required
def profile_details(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated successfully!'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'profile.html', {
        'form': form,
        'user': request.user
    })

@login_required
@user_passes_test(is_not_staff)
def get_collection_list(request):
    collections = request.user.collections.all()
    if request.method == 'POST':
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            messages.success(
                request,
                _('Collection "%(collection)s" created!') % {'collection': collection.name}
            )
            return redirect('users:collection_list')
    else:
        form = CollectionForm()
    
    return render(request, 'collection_list.html', {
        'collections': collections,
        'form': form
    })

@login_required
@user_passes_test(is_not_staff)
def get_collection_details(request, id):
    collection = get_object_or_404(Collection, pk=id, user=request.user)
    instruments = collection.instruments.all()
    return render(request, 'collection_details.html', {
        'collection': collection,
        'instruments': instruments
    })

@login_required
@user_passes_test(is_not_staff)
@require_POST
def delete_collection(request, id):
    collection = get_object_or_404(Collection, pk=id, user=request.user)
    name = collection.name
    collection.delete()
    messages.success(request, _('Collection "%(collection)s" deleted.') % {'collection': name})
    return redirect('users:collection_list')

@login_required
@user_passes_test(is_not_staff)
@require_POST
def create_collection_ajax(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'status': 'error', 'message': _('Invalid data.')}, status=400)
    
    if not name:
        return JsonResponse({'status': 'error', 'message': _('Name is required.')}, status=400)
    
    if request.user.collections.filter(name=name).exists():
        return JsonResponse(
            {'status': 'error', 'message': _('A collection with this name already exists.')},
            status=400
        )
    
    collection = Collection.objects.create(user=request.user, name=name)
    return JsonResponse({
        'status': 'success',
        'id': collection.id,
        'name': collection.name
    })

@login_required
@user_passes_test(is_not_staff)
def get_instrument_collections(request, instrument_id):
    instrument = get_object_or_404(Instrument, id=instrument_id)
    collections = request.user.collections.all().order_by('-is_default', 'name')
    
    data = []
    for col in collections:
        data.append({
            'id': col.id,
            'name': col.name,
            'is_checked': col.instruments.filter(id=instrument.id).exists(),
            'is_default': col.is_default,
        })
    
    return JsonResponse({
        'status': 'success',
        'collections': data
    })

@login_required
@user_passes_test(is_not_staff)
@require_POST
def toggle_collection_item(request, instrument_id):
    instrument = get_object_or_404(Instrument, id=instrument_id)

    collection_id = request.POST.get('collection_id')
    if not collection_id and request.content_type == 'application/json':
        try:
            collection_id = json.loads(request.body).get('collection_id')
        except (json.JSONDecodeError, AttributeError):
            pass

    if collection_id:
        collection = get_object_or_404(Collection, id=collection_id, user=request.user)
    else:
        collection = request.user.collections.filter(is_default=True).first() or \
                     request.user.collections.first()
        
        if not collection:
            collection = Collection.objects.create(
                user=request.user, 
                name=_('My Favorites'),
                is_default=True
            )
    
    if collection.instruments.filter(id=instrument.id).exists():
        collection.instruments.remove(instrument)
        added = False
        message = _('Removed %(instrument)s from %(collection)s.') % {
            'instrument': instrument.title,
            'collection': collection.name,
        }
    else:
        collection.instruments.add(instrument)
        added = True
        message = _('Added %(instrument)s to %(collection)s.') % {
            'instrument': instrument.title,
            'collection': collection.name,
        }
    
    return JsonResponse({
        'status': 'success',
        'added': added,
        'message': message,
        'collection_name': collection.name
    })

@login_required
@user_passes_test(is_not_staff)
def get_purchases_list(request):
    orders = request.user.orders.filter(status='completed').order_by('-created_at')
    return render(request, 'purchases_list.html', {'orders': orders})

@login_required
@user_passes_test(is_not_staff)
def get_purchase_details(request, id):
    order = get_object_or_404(Order, pk=id, user=request.user, status='completed')
    return render(request, 'purchase_details.html', {'order': order})
