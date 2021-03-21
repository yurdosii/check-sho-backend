from rest_framework.routers import DefaultRouter
from users import views as users_views


router = DefaultRouter()
router.register("users", users_views.UserViewSet)

urlpatterns = []
urlpatterns = router.urls

app_name = "api"
