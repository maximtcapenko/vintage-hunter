from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from django.core.paginator import Paginator
from django.db.models import Prefetch

from auction.models import Lot
from catalog.models import Category, Instrument, InstrumentImage

from commons.functional import DEFAULT_PAGE_SIZE

mcp = FastMCP(name='vintage-hunter')


@mcp.tool
def list_categories() -> list[dict]:
    """List all available instrument categories. Useful for discovering valid values for the 'category_id' filter in list_instruments."""
    categories = Category.objects.all().order_by('name')
    return [_serialize_category(c) for c in categories]


@mcp.tool
async def list_instruments(
    query: Annotated[Optional[str], Field(description='Natural language search using semantic similarity')] = None,
    category_id: Annotated[Optional[str], Field(description='Filter by category ID, ignored when query is set')] = None,
    page: Annotated[int, Field(ge=1, description='Page number')] = 1,
    page_size: Annotated[int, Field(ge=1, le=50, description='Results per page')] = DEFAULT_PAGE_SIZE,
) -> dict:
    """List instruments. Semantic search when query is set, category filter otherwise."""
    import asyncio
    from asgiref.sync import sync_to_async

    if query:
        from catalog.tasks import perform_mcp_vector_search

        task_result = perform_mcp_vector_search.delay(query, page_size)
        timeout = 15.0
        elapsed = 0.0
        poll_interval = 0.2

        while not task_result.ready():
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed >= timeout:
                return {
                    'error': 'Search task timed out',
                    'results': []
                }

        try:
            results = task_result.result
        except Exception as e:
            return {
                'error': f'Search task failed: {str(e)}',
                'results': []
            }

        return {
            'total': len(results),
            'page': 1,
            'total_pages': 1,
            'results': results,
        }

    def _fetch_instruments():
        images_prefetch = Prefetch('images', queryset=InstrumentImage.objects.all())
        auction_lot_prefetch = Prefetch(
            'auction_lot',
            queryset=Lot.objects.select_related('auction'),
            to_attr='prefetched_lot',
        )
        queryset = (
            Instrument.objects
            .query_without_embeddings()
            .exclude(is_new=True)
            .prefetch_related(auction_lot_prefetch, images_prefetch)
            .select_related('brand', 'category')
        )
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        return {
            'total': paginator.count,
            'page': current_page.number,
            'total_pages': paginator.num_pages,
            'results': [_serialize_instrument(i) for i in current_page],
        }

    return await sync_to_async(_fetch_instruments)()


@mcp.tool
def get_instrument_details(
    instrument_id: Annotated[str, Field(description='ID of the instrument to get details for')]
) -> dict:
    """Get detailed information about a specific instrument including technical specifications and similar items."""

    images_prefetch = Prefetch(
        'images',
        queryset=InstrumentImage.objects.order_by('-is_primary', 'id')
    )
    auction_lot_prefetch = Prefetch(
        'auction_lot',
        queryset=Lot.objects.select_related('auction'),
        to_attr='prefetched_lot',
    )

    try:
        instrument = (
            Instrument.objects
            .prefetch_related(images_prefetch, auction_lot_prefetch)
            .select_related('brand', 'category')
            .get(pk=instrument_id)
        )
    except Instrument.DoesNotExist:
        return {'error': 'Instrument not found'}

    similar_items = (
        Instrument.objects.find_visually_similar(instrument, limit=4)
        .select_related('brand', 'category')
        .prefetch_related(images_prefetch, auction_lot_prefetch)
    )

    return {
        'instrument': _serialize_instrument_detailed(instrument),
        'similar_items': [_serialize_instrument(item) for item in similar_items]
    }


def _serialize_instrument_detailed(i) -> dict:
    data = _serialize_instrument(i)
    data.update({
        'description': i.description,
        'specifications': i.specifications,
        'serial_number': i.serial_number,
        'is_original': i.is_original,
        'has_repairs': i.has_repairs,
        'is_concert_ready': i.is_concert_ready,
        'all_images': [img.image.url for img in i.images.all()],
    })
    return data


def _serialize_category(c) -> dict:
    return {
        'id': str(c.pk),
        'name': c.name,
        'description': c.description,
    }


def _serialize_instrument(i) -> dict:
    primary_image = next((img for img in i.images.all() if img.is_primary), None)

    lot = getattr(i, 'prefetched_lot', None)
    auction_data = None
    if lot:
        auction_data = {
            'lot_number': lot.lot_number,
            'status': lot.status,
            'starting_price': float(lot.starting_price),
            'estimated_price_min': float(lot.estimated_price_min),
            'estimated_price_max': float(lot.estimated_price_max),
            'expires_at': lot.expires_at.isoformat() if lot.expires_at else None,
            'auction_title': lot.auction.title,
            'auction_status': lot.auction.status,
        }

    return {
        'id': str(i.pk),
        'title': str(i),
        'category': i.category.name,
        'brand': i.brand.name,
        'year': i.year,
        'condition': str(i.condition_label),
        'price': float(i.price),
        'is_auction': i.is_auction,
        'is_sold': i.is_sold,
        'primary_image_url': primary_image.image.url if primary_image else None,
        'auction': auction_data,
    }
