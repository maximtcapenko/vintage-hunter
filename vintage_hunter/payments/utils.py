from django.conf import settings
from django.utils.module_loading import import_string

from .providers.base import BasePaymentProvider


class PaymentFactory:
    @staticmethod
    def get_provider() -> BasePaymentProvider:
        provider_path = getattr(settings, 'PAYMENT_PROVIDER', 'payments.providers.mock.MockPaymentProvider')
        provider_class = import_string(provider_path)
        return provider_class()
