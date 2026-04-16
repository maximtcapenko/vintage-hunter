from abc import abstractmethod


class BasePaymentProvider:
    @abstractmethod
    def process_payment(self, amount, currency, payment_details):
        pass
