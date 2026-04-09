from celery import shared_task

from .models import Instrument

@shared_task(bind=True)
def update_embeddings(self, instrumnet_id):
    instrument = Instrument.objects.get(pk=instrumnet_id)
    if not instrument:
        return
    
    instrument.update_embeddings()
