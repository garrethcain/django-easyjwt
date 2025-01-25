from django.utils.module_loading import import_string
from rest_framework.serializers import Serializer
from rest_framework import generics
from django.contrib.auth import get_user_model

from .settings import api_settings


User = get_user_model()


class TokenUserDetailView(generics.RetrieveAPIView):
    serializer_class = None
    _serializer_class = api_settings.USER_MODEL_SERIALIZER

    def get_serializer_class(self) -> Serializer:
        """
        If serializer_class is set when overridden, use it, otherwise get the class from settings.
        """

        if self.serializer_class:
            return self.serializer_class

        try:
            return import_string(self._serializer_class)
        except ImportError:
            msg = f"Could not import serializer '{self._serializer_class}'"
            raise ImportError(msg)

    def get_object(self):
        return self.request.user

    # The below was replaced by get_object. Not sure if requesting specific
    # users is required for some obscure usecase yet.
    # If this is still here, remove it please.

    # queryset = User.objects.all()
    #
    # def get_queryset(self):
    #     """
    #     Restrict the requesting user to only get what they
    #     have access too. This is not an Admin panel, you cannot
    #     see other user accounts regardless of privilege.
    #     """
    #     pk = self.kwargs.get("pk")
    #     user = self.request.user
    #     if any([user.is_staff, user.is_superuser]):
    #         return User.objects.filter(id=pk)
    #     return User.objects.filter(id=user.id)

    # def get(self, request, *args, **kwargs):
    #     # required to handle the case where the url is called iwth
    #     # a PK as a parameter.
    #     if not self.kwargs.get("pk"):
    #         self.kwargs["pk"] = request.user.pk
    #     return super().get(request, *args, **kwargs)
