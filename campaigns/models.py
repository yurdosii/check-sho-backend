from enum import Enum
from urllib.parse import urlparse

from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils.telegram import EMOJI

from . import helpers


class CampaignInterval(Enum):
    HOUR = "Every hour"
    DAY = "Every day"
    WEEK = "Every week"


# TODO
# parsers - singleton ???


class Campaign(models.Model):
    title = models.CharField(_("Title"), max_length=1024)
    description = models.CharField(
        _("Description"), null=True, blank=True, max_length=1024
    )
    market = models.ForeignKey(
        "campaigns.Market",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,  # TODO - think about it later
        blank=True,
        null=True,
    )

    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    INTERVAL_CHOICES = (
        (HOUR, "HOUR"),
        (DAY, "DAY"),
        (WEEK, "WEEK"),
    )
    interval = models.CharField(
        max_length=20, choices=INTERVAL_CHOICES, db_index=True, blank=True, null=True
    )

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Campaign: {self.title} by {self.owner}"

    @property
    def telegram_format(self):
        is_active = EMOJI["YES"] if self.is_active else EMOJI["NO"]

        result = f"""
*Campaign*: {self.title}
*Active*: {is_active}
        """

        items = [item.telegram_format for item in self.campaign_items.all()]
        # result_items = "\n".join(items)
        result_items = "".join(items)
        if items:
            result += f"""\n\nItems:\n{result_items}
            """
        else:
            result += "Items: 0"

        return result


# TODO (подумай) - різні налаштування CampaignItem, типу - "check price", "перевіряти наявність"
class CampaignItem(models.Model):
    title = models.CharField(_("Title"), max_length=1024, blank=True, null=True)
    description = models.CharField(
        _("Description"), null=True, blank=True, max_length=1024
    )

    url = models.URLField(max_length=255)

    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.CASCADE,
        related_name="campaign_items",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CampaignItem: {self.title} - {self.url}"

    @property
    def telegram_format(self):
        is_active = EMOJI["YES"] if self.is_active else EMOJI["NO"]

        # TODO - add name щоб був обов'язковий і шо
        # TODO - типу якщо не встановлює то щоб автоматично підтягувати
        result = f"""
_Url_: `{self.url}`
*Active*: {is_active}
        """
        return result

    # TODO - - validation by market url - думаю не


class Market(models.Model):
    title = models.CharField(_("Title"), max_length=1024)
    url = models.URLField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Market: {self.title} - {self.url}"

    @property
    def parser(self):
        return helpers.get_market_parser(self)

    def is_url_from_market(self, url):
        # TODO - https://allo.ua/ - така штука проходить, а не мала б
        market_url_parsed = urlparse(self.url)
        item_url_parsed = urlparse(url)

        return market_url_parsed.netloc == item_url_parsed.netloc


# TODO - (idea) - to track item's price протягом певного часу
# class MarketItem(models.Model):
#     title = models.CharField(_("Title"), max_length=1024)
#     url = models.CharField(max_length=255, validators=[NoSchemeURLValidator()])
#     # price =

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"MarketItem: {self.title} - {self.url}"
