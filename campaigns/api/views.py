import logging

from rest_framework import viewsets

from .. import models as campaigns_models
from . import serializers as campaigns_serializers

logger = logging.getLogger(__name__)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.Campaign.objects.all()
    serializer_class = campaigns_serializers.CampaignSerializer
    lookup_field = "pk"


class MarketViewSet(viewsets.ModelViewSet):
    queryset = campaigns_models.Market.objects.all()
    serializer_class = campaigns_serializers.MarketSerializer
    lookup_field = "pk"

    def list(self, request, *args, **kwargs):
        logger.info("Yura")
        logging.info("Yura")
        return super().list(self, request, *args, **kwargs)
