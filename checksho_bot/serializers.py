from rest_framework import serializers

from .models import TelegramUser


class TelegramUserSerializer(serializers.ModelSerializer):
    displayName = serializers.SerializerMethodField()

    def get_displayName(self, user):
        result = user.first_name
        if user.username:
            result = f"@{user.username}"
        elif user.last_name:
            result = f"{user.first_name} {user.last_name}"
        return result

    class Meta:
        model = TelegramUser
        exclude = []
