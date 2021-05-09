from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from campaigns import models as campaigns_models


class CampaignItemSerializers(serializers.ModelSerializer):
    class Meta:
        model = campaigns_models.CampaignItem
        exclude = []

    # TODO - url validation - make GET requests if not response.ok: raise validation error


class CampaignSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    market = serializers.SlugRelatedField(
        queryset=campaigns_models.Market.objects.all(), slug_field="title"
    )

    class Meta:
        model = campaigns_models.Campaign
        exclude = []
        expandable_fields = dict(
            items=dict(
                serializer="campaigns.api.serializers.CampaignItemSerializers",
                source="campaign_items",
                many=True,
            ),
            market_details=dict(
                serializer="campaigns.api.serializers.MarketSerializer", source="market"
            ),
            owner_details=dict(
                serializer="users.api.serializers.UserSerializer", source="owner"
            ),
        )


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = campaigns_models.Market
        exclude = []
