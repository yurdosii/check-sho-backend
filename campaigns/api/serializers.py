from rest_framework import serializers

from campaigns import models as campaigns_models


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = campaigns_models.Campaign
        exclude = []


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = campaigns_models.Market
        exclude = []
