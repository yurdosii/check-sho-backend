from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import \
    SerializerExtensionsMixin

from users.models import User


class UserSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):

    def get_profileStatistics(self, user: User):
        return user.profile_statistics

    class Meta:
        model = User
        exclude = []
        expandable_fields = dict(
            profileStatistics=serializers.SerializerMethodField
        )
