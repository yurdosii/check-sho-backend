from django.contrib import admin

from .models import Campaign, CampaignItem, Market


class CampaingItemInline(admin.TabularInline):
    model = CampaignItem


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    inlines = [CampaingItemInline]


@admin.register(CampaignItem)
class CampaignItemAdmin(admin.ModelAdmin):
    pass


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    pass
