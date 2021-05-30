from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from campaigns import models as campaigns_models


class CampaignItemListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        # maps for id->existing instance and id->data item.
        item_mapping = {item.id: item for item in instance}

        # get ids of items to delete
        item_ids = item_mapping.keys()
        data_ids = [item.get("id") for item in validated_data]

        # delete items
        ids_to_delete = list(set(item_ids) - set(data_ids))
        campaigns_models.CampaignItem.objects.filter(id__in=ids_to_delete).delete()

        # create / update items
        result = []
        for data in validated_data:
            data_id = data.pop("id", None)  # id is writable, but we don't want that
            item = item_mapping.get(data_id)
            if not item:
                result.append(self.child.create(data))
            else:
                result.append(self.child.update(item, data))

        return result


class CampaignItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        required=False
    )  # writable so we get it in validated_data
    types = serializers.MultipleChoiceField(
        choices=[item.name for item in campaigns_models.CampaignItemType],
        required=False,
        allow_null=True,
    )

    class Meta:
        model = campaigns_models.CampaignItem
        exclude = []
        list_serializer_class = CampaignItemListSerializer

    # TODO - url validation - make GET requests if not response.ok: raise validation error


class CampaignSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    market = serializers.SlugRelatedField(
        queryset=campaigns_models.Market.objects.all(), slug_field="title"
    )
    types = serializers.SerializerMethodField()
    campaign_items = CampaignItemSerializer(
        many=True, required=False
    )  # , write_only=True)

    def get_types(self, campaign):
        types = []
        for type in campaigns_models.CampaignType:
            attr = type.value
            if hasattr(campaign, attr) and getattr(campaign, attr):
                types.append(type.name)

        return types

    class Meta:
        model = campaigns_models.Campaign
        exclude = []
        expandable_fields = dict(
            items=dict(
                serializer="campaigns.api.serializers.CampaignItemSerializer",
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
