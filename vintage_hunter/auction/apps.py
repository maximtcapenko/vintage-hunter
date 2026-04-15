from django.apps import AppConfig


class AuctionConfig(AppConfig):
    name = 'auction'

    def ready(self):
        import auction.signals

