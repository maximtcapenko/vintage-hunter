from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from django.core.paginator import Paginator
from django.db.models import Prefetch

from auction.models import Lot
from catalog.models import Instrument, InstrumentImage

from commons.functional import DEFAULT_PAGE_SIZE

mcp = FastMCP(name='vintage-hunter')


@mcp.tool
def list_instruments(
    query: Annotated[Optional[str], Field(description='Natural language search using semantic similarity')] = None,
    category: Annotated[Optional[str], Field(description='Filter by category name (case-insensitive), ignored when query is set')] = None,
    page: Annotated[int, Field(ge=1, description='Page number')] = 1,
    page_size: Annotated[int, Field(ge=1, le=50, description='Results per page')] = DEFAULT_PAGE_SIZE,
) -> dict:
    """List instruments. Semantic search when query is set, category filter otherwise."""

    images_prefetch = Prefetch('images', queryset=InstrumentImage.objects.all())
    auction_lot_prefetch = Prefetch(
        'auction_lot',
        queryset=Lot.objects.select_related('auction'),
        to_attr='prefetched_lot',
    )

    if query:
        from pgvector.django import CosineDistance
        from catalog.services import EmbeddingService

        query_vector = EmbeddingService.encode(query)
        qs = (
            Instrument.objects
            .query_without_embeddings()
            .exclude(is_new=True)
            .prefetch_related(auction_lot_prefetch, images_prefetch)
            .select_related('brand', 'category')
            .order_by(CosineDistance('text_embedding', query_vector))
            [:page_size]
        )
        results = list(qs)
        return {
            'total': len(results),
            'page': 1,
            'total_pages': 1,
            'results': [_serialize_instrument(i) for i in results],
        }

    qs = (
        Instrument.objects
        .query_without_embeddings()
        .exclude(is_new=True)
        .prefetch_related(auction_lot_prefetch, images_prefetch)
        .select_related('brand', 'category')
    )
    if category:
        qs = qs.filter(category__name__iexact=category)

    paginator = Paginator(qs, page_size)
    current_page = paginator.get_page(page)
    return {
        'total': paginator.count,
        'page': current_page.number,
        'total_pages': paginator.num_pages,
        'results': [_serialize_instrument(i) for i in current_page],
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
