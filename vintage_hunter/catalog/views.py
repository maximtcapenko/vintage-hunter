from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _

from commons.functional import is_staff

from .forms import SearchCatalogForm, InstrumentForm, CategoryForm, BrandForm
from .models import Instrument, Category, Brand, InstrumentImage

DEFAULT_PAGE_SIZE = 50


@require_GET
def get_list(request):
    form = SearchCatalogForm(request.GET)
    
    def build_query_set():
        query = request.GET.get('q')
        if query:
            return Instrument.objects.search_by_text(query)

        return form.get_search_queryset(Instrument.objects.all())
    
    paginator = Paginator(build_query_set(), DEFAULT_PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    
    user_collection_instrument_ids = []
    if request.user.is_authenticated:
        from users.models import Collection
        user_collection_instrument_ids = Instrument.objects.filter(
            in_collections__user=request.user
        ).values_list('id', flat=True)

    return render(request, 'instruments_list.html', {
        'page': page,
        'total_count': paginator.count,
        'current_category': form.cleaned_data.get('category') if form.is_valid() else None,
        'categories': Category.objects.all(),
        'user_collection_instrument_ids': user_collection_instrument_ids
    })


@require_GET
def get_details(request, id):
    instrument = get_object_or_404(Instrument.objects.prefetch_related(Prefetch(
        'images', queryset=InstrumentImage.objects.order_by('-is_primary')
    )), pk=id)
    similar_items = Instrument.objects.find_visually_similar(instrument, limit=4)
    
    user_collection_instrument_ids = []
    if request.user.is_authenticated and not request.user.is_staff:
        user_collection_instrument_ids = Instrument.objects.filter(
            in_collections__user=request.user
        ).values_list('id', flat=True)

    return render(request, 'instrument_details.html', {
        'instrument': instrument,
        'similar_items': similar_items,
        'user_collection_instrument_ids': user_collection_instrument_ids
    })

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def create_instrument(request):
    if request.method == "POST":
        form = InstrumentForm(request.POST)
        if form.is_valid():
            instrument = form.save()
            messages.success(
                request,
                _('Instrument "%(instrument)s" created. Now you can add photos.') % {'instrument': instrument}
            )
            return redirect('catalog:edit_instrument', id=instrument.id)
    else:
        form = InstrumentForm()
        
    return render(request, 'instrument_form.html', {
        'form': form,
        'title': _('Add New Instrument')
    })

@user_passes_test(is_staff)
@require_GET
def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'catalog/category_list.html', {'categories': categories})

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def create_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(
                request,
                _('Category "%(category)s" created.') % {'category': category.name}
            )
            return redirect('catalog:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'catalog/category_form.html', {
        'form': form,
        'title': _('Create New Category')
    })

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def edit_category(request, id):
    category = get_object_or_404(Category, pk=id)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Category "%(category)s" updated.') % {'category': category.name}
            )
            return redirect('catalog:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'catalog/category_form.html', {
        'form': form,
        'category': category,
        'title': _('Edit Category: %(category)s') % {'category': category.name}
    })

@user_passes_test(is_staff)
@require_GET
def brand_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'catalog/brand_list.html', {'brands': brands})

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def create_brand(request):
    if request.method == "POST":
        form = BrandForm(request.POST)
        if form.is_valid():
            brand = form.save()
            messages.success(
                request,
                _('Brand "%(brand)s" created.') % {'brand': brand.name}
            )
            return redirect('catalog:brand_list')
    else:
        form = BrandForm()
    
    return render(request, 'catalog/brand_form.html', {
        'form': form,
        'title': _('Create New Brand')
    })

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def edit_brand(request, id):
    brand = get_object_or_404(Brand, pk=id)
    if request.method == "POST":
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Brand "%(brand)s" updated.') % {'brand': brand.name}
            )
            return redirect('catalog:brand_list')
    else:
        form = BrandForm(instance=brand)
    
    return render(request, 'catalog/brand_form.html', {
        'form': form,
        'brand': brand,
        'title': _('Edit Brand: %(brand)s') % {'brand': brand.name}
    })

@user_passes_test(is_staff)
@require_POST
def upload_instrument_image(request, instrument_id):
    instrument = get_object_or_404(Instrument, id=instrument_id)
    images = request.FILES.getlist('images')
    
    if images:
        for image_file in images:
            InstrumentImage.objects.create(
                instrument=instrument,
                image=image_file,
                is_primary=not instrument.images.exists()
            )
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': _('No images uploaded.')}, status=400)

@user_passes_test(is_staff)
@require_POST
def set_primary_image(request, image_id):
    image = get_object_or_404(InstrumentImage, id=image_id)
    
    InstrumentImage.objects.filter(instrument=image.instrument).update(is_primary=False)
    
    image.is_primary = True
    image.save()
    
    return JsonResponse({
        'status': 'success',
        'message': _('Image set as primary.'),
        'image_id': image.id
    })

@user_passes_test(is_staff)
@require_POST
def delete_instrument_image(request, image_id):
    image = get_object_or_404(InstrumentImage, id=image_id)
    instrument = image.instrument
    
    if instrument.images.count() <= 1:
        return JsonResponse({
            'status': 'error', 
            'message': _('Cannot delete the last image. An instrument must have at least one photo.')
        }, status=400)
    
    was_primary = image.is_primary
    image.delete()
    
    if was_primary:
        next_primary = instrument.images.first()
        if next_primary:
            next_primary.is_primary = True
            next_primary.save()
            
    return JsonResponse({'status': 'success'})

@user_passes_test(is_staff)
@require_http_methods(["GET", "POST"])
def edit_instrument(request, id):
    instrument = get_object_or_404(Instrument, pk=id)
    images = instrument.images.all().order_by('-is_primary', 'id')

    if request.method == "POST":
        form = InstrumentForm(request.POST, instance=instrument)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Instrument "%(instrument)s" updated.') % {'instrument': instrument}
            )
            return redirect('catalog:get_details', id=instrument.id)
    else:
        form = InstrumentForm(instance=instrument)
        
    return render(request, 'instrument_form.html', {
        'form': form,
        'images': images,
        'instrument': instrument,
        'title': _('Edit %(instrument)s') % {'instrument': instrument}
    })
