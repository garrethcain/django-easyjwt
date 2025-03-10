from django.utils.module_loading import import_string
from django.contrib.auth import get_user_model
from rest_framework import generics


from .settings import api_settings


User = get_user_model()


class TokenUserDetailView(generics.RetrieveAPIView):
    serializer_class = None
    _serializer_class = api_settings.USER_MODEL_SERIALIZER

    def get_serializer_class(self):
        """
        If serializer_class is set when overridden, use it, otherwise get the class from settings.
        """

        if self.serializer_class:
            return self.serializer_class  # type: ignore

        try:
            return import_string(self._serializer_class)
        except ImportError:
            msg = f"Could not import serializer '{self._serializer_class}'"
            raise ImportError(msg)

    def get_object(self):
        return self.request.user
