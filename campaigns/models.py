from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import helpers


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


# TODO - (idea) - to track item's price протягом певного часу
# class MarketItem(models.Model):
#     title = models.CharField(_("Title"), max_length=1024)
#     url = models.CharField(max_length=255, validators=[NoSchemeURLValidator()])
#     # price =

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"MarketItem: {self.title} - {self.url}"
