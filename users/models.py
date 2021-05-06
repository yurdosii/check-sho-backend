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

    @property
    def profile_statistics(self):
        # markets: {"market_name": "number of campaigns by market"}
        # number of campaigns: int
        # number of items: int

        campaigns = self.campaigns.select_related("market").prefetch_related("campaign_items")

        # markets
        markets_titles = list(map(lambda market: market.title, Market.objects.all()))
        campaigns_by_market = dict.fromkeys(markets_titles, 0)
        for campaign in campaigns:
            campaigns_by_market[campaign.market.title] += 1
        
        # campaigns number
        campaigns_number = len(campaigns)

        # items number
        items_number = sum(map(
            lambda campaign: campaign.campaign_items.count(), campaigns
        ))

        # result
        result = {
            "markets": campaigns_by_market,
            "campaigns_number": campaigns_number,
            "items_number": items_number,
        }

        return result
