from django.db.models import signals
from django.dispatch import receiver

from .models import Instrument, InstrumentImage
from .tasks import update_embeddings


@receiver(signals.post_save, sender=Instrument)
def trigger_embeddings_update(sender, instance, created, **kwargs):
    update_fields = kwargs.get('update_fields')
    if update_fields and ('text_embedding' in update_fields or 'image_embedding' in update_fields):
        return

    update_embeddings.delay(instance.id)


@receiver(signals.post_save, sender=InstrumentImage)
def trigger_image_embeddings_update(sender, instance, created, **kwargs):
    if created and instance.is_primary:
        update_embeddings.delay(instance.id)
