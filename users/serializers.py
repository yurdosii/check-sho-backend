from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        # fields = [
        #     "pk",
        #     "username",
        #     "first_name",
        #     "last_name",
        #     "email",
        #     "type",
        #     "is_superuser",
        # ]
