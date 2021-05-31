from rest_framework import serializers
from rest_framework_serializer_extensions.serializers import SerializerExtensionsMixin

from checksho_bot.serializers import TelegramUserSerializer
from users.models import User


class UserSerializer(SerializerExtensionsMixin, serializers.ModelSerializer):
    telegram_user = TelegramUserSerializer(required=False)

    def get_profileStatistics(self, user: User):
        return user.profile_statistics

    class Meta:
        model = User
        exclude = []
        expandable_fields = dict(profileStatistics=serializers.SerializerMethodField)


class TelegramResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    username = serializers.CharField(required=False)
    photo_url = serializers.URLField(required=False)
    auth_date = serializers.IntegerField(required=False)
    hash = serializers.CharField(required=False)
