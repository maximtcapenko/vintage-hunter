from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):
        from .signals import trigger_embeddings_update
        from .services import EmbeddingService, ImageVectorService

        EmbeddingService.load_model()
        ImageVectorService.load_model()
        return super().ready()
