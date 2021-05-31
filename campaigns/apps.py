from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    name = "campaigns"

    def ready(self):
        try:
            from . import signals  # noqa F401
        except ImportError:
            pass
