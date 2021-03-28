from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from utils.email import send_email_message

from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "pk"

    @action(detail=False, methods=["get"])
    def test_email(self, request):
        send_email_message(
            subject="Subject test 1",
            body="Body test 1",
            to=["yurdosii.ksv@gmail.com"]
        )
        return Response({"status": "sent"})
