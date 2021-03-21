from rest_framework.routers import DefaultRouter
from users.api import views as users_views
from campaigns.api import views as campaigns_views


router = DefaultRouter()
router.register("users", users_views.UserViewSet)
router.register("campaigns", campaigns_views.CampaignViewSet)
router.register("markets", campaigns_views.MarketViewSet)

urlpatterns = []
urlpatterns = router.urls

app_name = "api"
