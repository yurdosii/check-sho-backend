from django.db import models
from django.utils.translation import ugettext_lazy as _


# TODO
# - complex campaigns (2 markets)
# CampaignItem model to make it difficult


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Campaign: {self.title} by {self.owner.username}"


class Market(models.Model):
    title = models.CharField(_("Title"), max_length=1024)
    url = models.URLField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Market: {self.title} - {self.url}"


# class MarketItem(models.Model):
#     title = models.CharField(_("Title"), max_length=1024)
#     url = models.CharField(max_length=255, validators=[NoSchemeURLValidator()])
#     # price =

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"MarketItem: {self.title} - {self.url}"
