from django.utils.module_loading import import_string
from rest_framework.serializers import Serializer
from django.shortcuts import render
from rest_framework import generics
from django.contrib.auth import get_user_model

from .settings import api_settings
from .serializers import TokenUserSerializer


User = get_user_model()


class TokenUserDetailView(generics.RetrieveAPIView):
    # serializer_class = TokenUserSerializer
    serializer_class = None
    _serializer_class = api_settings.USER_MODEL_SERIALIZER

    def get_serializer_class(self) -> Serializer:
        """
        If serializer_class is set, use it directly. Otherwise get the class from settings.
        """

        if self.serializer_class:
            return self.serializer_class

        try:
            return import_string(self._serializer_class)
        except ImportError:
            msg = f"Could not import serializer '{self._serializer_class}'"
            raise ImportError(msg)

    queryset = User.objects.all()

    def get_queryset(self):
        """
        Restrict the requesting user to only get what they
        have access too.
        """
        pk = self.kwargs.get("pk")
        user = self.request.user
        if any([user.is_staff, user.is_superuser]):
            return User.objects.filter(id=pk)
        return User.objects.filter(id=user.id)
