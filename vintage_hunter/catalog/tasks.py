from celery import shared_task
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from auction.models import Lot
from commons.sse import broadcast_event
from .models import Instrument, InstrumentImage

@shared_task(bind=True)
def update_embeddings(self, instrument_id):
    instrument = Instrument.objects.filter(pk=instrument_id).first()
    if not instrument:
        return
    
    instrument.update_embeddings()

@shared_task
def perform_vector_search(user_id, query_text, language_code):
    from django.utils import translation
    
    translation.activate(language_code)
    
    from commons.functional import SEARCH_RESULTS_LIMITS
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        return

    results = Instrument.objects.search_by_text(query_text)
    
    images_prefetch = Prefetch(
        'images',
        queryset=InstrumentImage.objects.all()
    )
    auction_lot_prefetch = Prefetch(
        'auction_lot',
        queryset=Lot.objects.select_related('auction'),
        to_attr='prefetched_lot'
    )
    
    results = results.exclude(is_new=True).prefetch_related(
        images_prefetch,
        auction_lot_prefetch,
        'brand'
    )[:SEARCH_RESULTS_LIMITS]
    
    user_collection_instrument_ids = Instrument.objects.filter(
        in_collections__user=user
    ).values_list('id', flat=True)

    html_results = ""
    for instrument in results:
        html_results += render_to_string(
            'catalog/includes/instrument_card.html',
            {
                'instrument': instrument,
                'user': user,
                'user_collection_instrument_ids': list(user_collection_instrument_ids)
            }
        )
    
    from django.utils.translation import ngettext
    count_text = ngettext(
        "Found %(count)d item",
        "Found %(count)d items",
        len(results)
    ) % {'count': len(results)}

    broadcast_event(
        f'user:{user_id}', 
        'search_results', 
        {
            'query': query_text,
            'html': html_results,
            'count': len(results),
            'count_text': count_text
        }
    )
