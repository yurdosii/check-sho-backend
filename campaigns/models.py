from enum import Enum
from urllib.parse import urlparse
from datetime import timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _
from multiselectfield import MultiSelectField

from utils.telegram import EMOJI

from . import helpers


class CampaignInterval(Enum):
    HOUR = "Every hour"
    DAY = "Every day"
    WEEK = "Every week"


class CampaignIntervalTimedelta(Enum):
    HOUR = timedelta(hours=1)
    DAY = timedelta(days=1)
    WEEK = timedelta(days=7)


class CampaignType(Enum):
    TELEGRAM = "is_telegram_campaign"
    EMAIL = "is_email_campaign"


class CampaignItemType(Enum):
    CHECK_PRICE = "Check price"
    CHECK_SALE = "Check sale"


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
        related_name="campaigns",
        on_delete=models.SET_NULL,
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
    is_telegram_campaign = models.BooleanField(default=False)
    is_email_campaign = models.BooleanField(default=False)

    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Campaign: {self.title} by {self.owner}"

    @property
    def telegram_format(self):
        # TODO - remove probably
        is_active = EMOJI[self.is_active]

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

    @property
    def campaign_type(self):
        # TODO - whether it is use
        types = []

        if self.is_telegram_campaign:
            types.append("Telegram")
        if self.is_email_campaign:
            types.append("Email")

        type = "Not set"
        if types:
            type = ", ".join(types)
        return type

    def run_campaign(self):
        results = helpers.get_campaign_results(self)
        # results = list(map(lambda result: result.to_dict(), results_objects))
        return results

    def run_telegram_campaign(self):
        results = self.run_campaign()
        # breakpoint()
        return results


# TODO (подумай) - різні налаштування CampaignItem, типу - "check price", "перевіряти наявність"
# TODO - title shouldn't be empty, if user don't provide it, parse it from page on creation
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

    types = MultiSelectField(
        max_length=50,
        choices=[[type.name, type.value] for type in CampaignItemType],
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CampaignItem: {self.title} - {self.url}"

    @property
    def telegram_format(self):
        # TODO - remove probably
        is_active = EMOJI[self.is_active]

        # TODO - add name щоб був обов'язковий і шо
        # TODO - типу якщо не встановлює то щоб автоматично підтягувати
        result = f"""
_Url_: `{self.url}`
*Active*: {is_active}
        """
        return result


class Market(models.Model):
    title = models.CharField(_("Title"), max_length=1024, unique=True)
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
