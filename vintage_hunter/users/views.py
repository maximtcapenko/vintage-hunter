from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import UserProfileForm, CollectionForm
from .models import Collection
from catalog.models import Instrument

from django.core.exceptions import PermissionDenied

def is_not_staff(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def profile_details(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'profile.html', {
        'form': form,
        'user': request.user
    })

@login_required
@is_not_staff
def get_collection_list(request):
    collections = request.user.collections.all()
    if request.method == 'POST':
        form = CollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            messages.success(request, f'Collection "{collection.name}" created!')
            return redirect('users:collection_list')
    else:
        form = CollectionForm()
    
    return render(request, 'collection_list.html', {
        'collections': collections,
        'form': form
    })

@login_required
@is_not_staff
def get_collection_details(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    instruments = collection.instruments.all()
    return render(request, 'collection_details.html', {
        'collection': collection,
        'instruments': instruments
    })

@login_required
@is_not_staff
@require_POST
def delete_collection(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    name = collection.name
    collection.delete()
    messages.success(request, f'Collection "{name}" deleted.')
    return redirect('users:collection_list')

@login_required
@is_not_staff
@require_POST
def toggle_collection_item(request, instrument_id):
    instrument = get_object_or_404(Instrument, id=instrument_id)
    
    # Support both JSON body and FormData
    collection_id = request.POST.get('collection_id')
    if not collection_id and request.content_type == 'application/json':
        import json
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
                name="My Favorites", 
                is_default=True
            )
    
    if collection.instruments.filter(id=instrument.id).exists():
        collection.instruments.remove(instrument)
        added = False
        message = f'Removed {instrument.title} from {collection.name}'
    else:
        collection.instruments.add(instrument)
        added = True
        message = f'Added {instrument.title} to {collection.name}'
    
    return JsonResponse({
        'status': 'success',
        'added': added,
        'message': message,
        'collection_name': collection.name
    })
