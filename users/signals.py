from django.db.models import signals
from django.dispatch import receiver

from . import models, helpers


@receiver(signals.post_save, sender=models.User)
def set_role_on_creation(instance, **kwargs):
    created = kwargs.get("created")
    if created:
        helpers.set_user_role_on_creation(instance)
