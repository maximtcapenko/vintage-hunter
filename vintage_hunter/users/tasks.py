from datetime import timedelta

from django.db.models import F, Q
from django.db.models.functions import Now
from django.utils import timezone

from celery import shared_task

from pgvector.django import CosineDistance

from .models import InstrumentFinder, Instrument, InstrumentFinderResult

@shared_task
def run_user_search(job_id):
    finder = InstrumentFinder.objects.filter(pk=job_id, is_active=True).first()
    if not finder:
        return

    queryset = Instrument.objects.filter(is_sold=False, is_draft=False)
    exclude_ids = finder.results.values_list('instrument_id', flat=True)
    queryset = queryset.exclude(id__in=exclude_ids)

    if finder.brand:
        queryset = queryset.filter(brand=finder.brand)
    if finder.category:
        queryset = queryset.filter(category=finder.category)

    if finder.availability == 'buy_it_now':
        queryset = queryset.filter(is_auction=False)
    elif finder.availability == 'auction':
        queryset = queryset.filter(is_auction=True)

    if finder.query_text_embedding:
        queryset = queryset.order_by(
            CosineDistance('text_embedding', finder.query_text_embedding))

    for result in queryset[:finder.max_results]:
        InstrumentFinderResult.objects.get_or_create(instrument=result, finder=finder)

@shared_task
def check_finder_next_run():
    next_runs = InstrumentFinder.objects.filter(
        is_active=True
    ).filter(
        Q(last_run_at__isnull=True) | 
        Q(last_run_at__lte=Now() - F('frequency_minutes') * timedelta(minutes=1))
    )

    for next_run in next_runs:
        run_user_search.delay(next_run.id)
        next_run.last_run_at = timezone.now()
        next_run.save(update_fields=['last_run_at'])
