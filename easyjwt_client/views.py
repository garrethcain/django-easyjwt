from rest_framework import generics, permissions, response
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.conf import settings
from django.http import HttpResponseRedirect


from .serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from .utils import TokenManager


class PasswordChangeDoneView(TemplateView):
    template_name = "registration/password_change_done.html"


class PasswordChangeView(BasePasswordChangeView):
    template_name = "registration/password_change_form.html"  # Custom template
    success_url = reverse_lazy("password_change_done")  # Redirect after success

    def post(self, request):
        tokenmanager = TokenManager()
        data = request.POST.copy()
        username = getattr(request.user, tokenmanager.username_field)
        tokenmanager.password_change(
            username,
            data.get("old_password"),
            data.get("new_password1"),
        )
        return HttpResponseRedirect(self.get_success_url())


class PasswordResetView(RedirectView):
    # Optional: Set whether the redirect is permanent
    permanent = False  # Set to True for a permanent redirect (301)
    # Optional: Include query strings in the redirect
    query_string = True  # Set to False to ignore query strings

    # Optional: Dynamically generate the redirect URL
    def get_redirect_url(self, *args, **kwargs):
        return f"{settings.EASY_JWT['REMOTE_AUTH_SERVICE_URL']}/accounts/password_reset/"


class TokenObtainPairView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokens = tokenmanager.authenticate(**serializer.validated_data)

        return response.Response(tokens)


class TokenRefreshView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokens = tokenmanager.refresh(**serializer.validated_data)

        return response.Response(tokens)


class TokenVerifyView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenVerifySerializer

    def post(self, request):
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokenmanager.verify(**serializer.validated_data)

        return response.Response({})
