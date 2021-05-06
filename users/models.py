from collections import defaultdict

from django.contrib.auth.models import AbstractUser
from django.db import models

from campaigns.models import Market
from checksho_bot.models import TelegramUser


class User(AbstractUser):
    ADMIN = "ADMIN"
    USER = "USER"
    CUSTOM_ROLE_CHOICES = (
        (ADMIN, "ADMIN"),
        (USER, "USER"),
    )
    role = models.CharField(max_length=20, choices=CUSTOM_ROLE_CHOICES, db_index=True)
    telegram_user = models.OneToOneField(
        TelegramUser, on_delete=models.SET_NULL, blank=True, null=True
    )

    # TODO
    # send_email = boolean  # чи відправляти на пошту
    # send_telegram - boolean  # чи відправляти на телегу
    # send_notifications - boolean # чи загалом відсилати, типу офнути взагалі

    def __str__(self):
        return self.username
