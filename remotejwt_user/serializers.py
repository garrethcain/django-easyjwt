# from django.contrib.auth.models import User
from rest_framework import serializers

from django.contrib.auth import get_user_model

User = get_user_model()


class TokenUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "email",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        read_only_fields = ("date_joined", "last_login", "is_staff", "is_superuser")
