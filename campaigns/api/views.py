import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from .. import helpers as campaigns_helpers
from .. import models as campaigns_models
from . import serializers as campaigns_serializers

logger = logging.getLogger(__name__)


class CampaignViewSet(SerializerExtensionsAPIViewMixin, viewsets.ModelViewSet):
    queryset = campaigns_models.Campaign.objects.all()
    serializer_class = campaigns_serializers.CampaignSerializer
    lookup_field = "pk"

    @action(detail=True, methods=["post"])
    def run_campaign(self, request, **kwargs):
        # TODO - only campaign's owner can run campaign (add validation)
        campaign = self.get_object()
        if not campaign.is_active:
            return Response(
                {"error": "Campaign isn't active"}, status=status.HTTP_400_BAD_REQUEST
            )

        results = campaigns_helpers.run_endpoint_campaign(campaign)

        return Response(results)

    @action(detail=True, methods=["post"])
    def test_email_campaign(self, request, **kwargs):
        campaign = self.get_object()
        if not campaign.is_active:
            return Response(
                {"error": "Campaign isn't active"}, status=status.HTTP_400_BAD_REQUEST
            )

        owner = campaign.owner
        if not owner or not owner.email:
            return Response(
                {"error": "Owner's email isn't set"}, status=status.HTTP_400_BAD_REQUEST
            )

        results = campaigns_helpers.run_email_campaign(campaign)

        return Response(results)


class MarketViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.Market.objects.all()
    serializer_class = campaigns_serializers.MarketSerializer
    lookup_field = "pk"

    def list(self, request, *args, **kwargs):
        logger.info("Yura")
        logging.info("Yura")
        return super().list(self, request, *args, **kwargs)


class CampaignItemViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.CampaignItem.objects.all()
    serializer_class = campaigns_serializers.CampaignItemSerializers
    lookup_field = "pk"

    def get_queryset(self):
        return campaigns_models.CampaignItem.objects.filter(
            campaign__pk=self.kwargs["campaign_pk"]
        )

    @action(detail=False, methods=["post"])
    def create_list(self, request, **kwargs):
        campaign_pk = self.kwargs["campaign_pk"]
        data = list(map(lambda item: {**item, "campaign": campaign_pk}, request.data))

        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, **kwargs):
        request.data["campaign"] = self.kwargs["campaign_pk"]
        return super().create(request, **kwargs)
