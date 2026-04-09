from django.db import models
from pgvector.django import CosineDistance

SEARCH_RESULTS_LIMITS = 25

class InstrumentManager(models.Manager):

    def search_by_text(self, query_text, limit=SEARCH_RESULTS_LIMITS):
        if not query_text or not query_text.strip():
            return self.get_queryset().none()
        
        from .services import EmbeddingService
        query_vector = EmbeddingService.encode(query_text)
        
        return self.get_queryset().order_by(
            CosineDistance('text_embedding', query_vector))[:limit]


    def find_visually_similar(self, instrument, limit=SEARCH_RESULTS_LIMITS):
        if instrument.image_embedding is None or len(instrument.image_embedding) == 0:
            return self.none()
        
        return self.get_queryset().exclude(id=instrument.id) \
        .order_by(CosineDistance('image_embedding', instrument.image_embedding))[:limit]
