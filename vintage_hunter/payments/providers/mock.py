import uuid

from .base import BasePaymentProvider


class MockPaymentProvider(BasePaymentProvider):
    def process_payment(self, amount, currency, payment_details):
        return {
            'status': 'success',
            'transaction_id': f"mock_{uuid.uuid4().hex[:12]}",
            'message': 'Payment processed successfully (Mock)'
        }
