from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .forms import SearchCatalogForm
from .models import Instrument, Category, InstrumentImage

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
    
    return render(request, 'instrument_details.html', {
        'instrument': instrument,
        'similar_items': similar_items,
    })
