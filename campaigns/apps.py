from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    name = "campaigns"

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
