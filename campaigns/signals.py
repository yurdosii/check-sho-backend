from django.db.models import signals
from django.dispatch import receiver

from . import helpers, models


@receiver(signals.post_save, sender=models.CampaignItem)
def update_item_title_on_creation(instance, **kwargs):
    created = kwargs.get("created")
    if created:
        helpers.check_item_title_on_creation(instance)


@receiver(signals.post_save, sender=models.Campaign)
def update_campaign_next_run_on_save(instance, **kwargs):
    if instance.is_active and not instance.next_run:
        helpers.update_campaign_next_run(instance)
