from django.db.models import signals
from django.dispatch import receiver

from checksho_bot.models import TelegramUser

from . import helpers, models


@receiver(signals.post_save, sender=models.User)
def set_role_on_creation(instance, **kwargs):
    created = kwargs.get("created")
    if created:
        helpers.set_user_role_on_creation(instance)


@receiver(signals.post_save, sender=TelegramUser)
def create_user_on_telegram_user_creation(instance, **kwargs):
    """
    Don't know how to init signals in checksho_bot (no apps.py file)
    so to not break anything I'll just call it here
    """
    created = kwargs.get("created")
    if created:
        helpers.create_user_for_telegram_user(instance)
