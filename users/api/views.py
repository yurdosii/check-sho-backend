from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from users.helpers import link_telegram_user_to_user
from users.models import User
from utils.emails import send_email_message

from .serializers import TelegramResponseSerializer, UserSerializer


class UserViewSet(SerializerExtensionsAPIViewMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "pk"
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def test_email(self, request):
        send_email_message(
            subject="Subject test 1", body="Body test 1", to=["yurdosii.ksv@gmail.com"]
        )
        return Response({"status": "sent"})

    @action(detail=True, methods=["post"])
    def link_telegram(self, request, *args, **kwargs):
        user = self.get_object()

        serializer = TelegramResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        updated_user = link_telegram_user_to_user(user, serializer.validated_data)
        user_serializer = self.get_serializer(updated_user)

        return Response(user_serializer.data)
