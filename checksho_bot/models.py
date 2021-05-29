from django.db import models
from django.db.models import CASCADE
from django_tgbot.models import (
    AbstractTelegramChat,
    AbstractTelegramState,
    AbstractTelegramUser,
)

from campaigns.models import Campaign


class TelegramUser(AbstractTelegramUser):
    @property
    def user_campaigns(self):
        campaigns = []
        user = getattr(self, "user", None)
        if user:
            campaigns = Campaign.objects.filter(owner=user)
        return campaigns


class TelegramChat(AbstractTelegramChat):
    pass


class TelegramState(AbstractTelegramState):
    telegram_user = models.ForeignKey(
        TelegramUser,
        related_name="telegram_states",
        on_delete=CASCADE,
        blank=True,
        null=True,
    )
    telegram_chat = models.ForeignKey(
        TelegramChat,
        related_name="telegram_states",
        on_delete=CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = ("telegram_user", "telegram_chat")
