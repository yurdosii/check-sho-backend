from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from users.api import views as users_views
from campaigns.api import views as campaigns_views


router = DefaultRouter()
router.register("users", users_views.UserViewSet)
router.register("campaigns", campaigns_views.CampaignViewSet)
router.register("markets", campaigns_views.MarketViewSet)

# nested routers
nested_router = NestedDefaultRouter

campaigns_router = nested_router(router, "campaigns", lookup="campaign")
campaigns_router.register(
    "campaign-items",
    campaigns_views.CampaignItemViewSet,
    basename="campaign-campaign_items",
)

urlpatterns = []
urlpatterns += router.urls
urlpatterns += campaigns_router.urls

app_name = "api"
