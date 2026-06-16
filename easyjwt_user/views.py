from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


from .settings import api_settings


User = get_user_model()


class TokenUserDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get_serializer_class(self):
        """
        If serializer_class is set when overridden, use it, otherwise get the class from settings.
        """

        if self.serializer_class:
            return self.serializer_class  # type: ignore

        try:
            return import_string(api_settings.USER_MODEL_SERIALIZER)
        except ImportError:
            msg = f"Could not import serializer '{api_settings.USER_MODEL_SERIALIZER}'"
            raise ImportError(msg)

    def get_object(self):
        return self.request.user
