from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_serializer_extensions.views import \
    SerializerExtensionsAPIViewMixin

from users.models import User
from utils.emails import send_email_message

from .serializers import UserSerializer


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
