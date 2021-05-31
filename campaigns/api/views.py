import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from .. import helpers as campaigns_helpers
from .. import models as campaigns_models
from .. import tasks as campaigns_tasks
from . import serializers as campaigns_serializers


logger = logging.getLogger(__name__)


class CampaignViewSet(SerializerExtensionsAPIViewMixin, viewsets.ModelViewSet):
    queryset = campaigns_models.Campaign.objects.all()
    serializer_class = campaigns_serializers.CampaignSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user).order_by("-updated_at")

    @action(detail=True, methods=["post"])
    def run_endpoint_campaign(self, request, **kwargs):
        campaign = self.get_object()
        if not campaign.is_active:
            return Response(
                {"error": "Campaign isn't active"}, status=status.HTTP_400_BAD_REQUEST
            )

        results = campaigns_helpers.run_endpoint_campaign(campaign)
        campaigns_tasks.debug_task.delay()

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

    @action(detail=True, methods=["post"])
    def run_campaign(self, request, **kwargs):
        campaign = self.get_object()
        if campaign.owner != request.user:
            return Response(
                {"error": "You are not an owner of this campaign"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not campaign.is_telegram_campaign and not campaign.is_email_campaign:
            return Response(
                {"error": "Campaign's type (Telegram or email) should be set"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not campaign.is_active:
            return Response(
                {"error": "Set campaign's active to be able to run it"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not campaign.campaign_items.exists():
            return Response(
                {"error": "No campaign items to run"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification_message = campaigns_helpers.run_campaign(request.user, campaign)

        return Response({"notification": notification_message})

    @action(detail=False, methods=["post"])
    def run_scheduled_campaigns(self, request):
        """
        To check celery task run_scheduled_campaigns by endpoint
        """
        campaigns_tasks.run_scheduled_campaigns.delay()
        return Response({"status": "done"})


class MarketViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.Market.objects.all()
    serializer_class = campaigns_serializers.MarketSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        logger.info("Yura")
        logging.info("Yura")
        return super().list(self, request, *args, **kwargs)


class CampaignItemViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.CampaignItem.objects.all()
    serializer_class = campaigns_serializers.CampaignItemSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return campaigns_models.CampaignItem.objects.filter(
            campaign__pk=self.kwargs["campaign_pk"]
        )

    def get_campaign(self):
        campaign = campaigns_models.Campaign.objects.get(id=self.kwargs["campaign_pk"])
        return campaign

    @action(detail=False, methods=["post"])
    def create_list(self, request, **kwargs):
        campaign_pk = self.kwargs["campaign_pk"]
        data = list(map(lambda item: {**item, "campaign": campaign_pk}, request.data))

        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put", "patch"])
    def update_list(self, request, **kwargs):
        campaign_pk = self.kwargs["campaign_pk"]
        campaign = self.get_campaign()

        items = campaign.campaign_items.all()
        data = list(map(lambda item: {**item, "campaign": campaign_pk}, request.data))

        serializer = self.get_serializer(items, data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, **kwargs):
        request.data["campaign"] = self.kwargs["campaign_pk"]
        return super().create(request, **kwargs)
