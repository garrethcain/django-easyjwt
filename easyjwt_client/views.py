import logging
from urllib.parse import urlsplit

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from rest_framework import exceptions, generics, permissions, response, status

from .serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from .settings import api_settings
from .utils import TokenManager

logger = logging.getLogger("easyjwt_client")


# ---------------------------------------------------------------------------
# Refresh-token cookie helpers
# ---------------------------------------------------------------------------
# Cookie mode is opt-in (REFRESH_TOKEN_IN_COOKIE, default False). When enabled,
# the refresh token is stored in an HttpOnly cookie and removed from the JSON
# body so it is never exposed to JavaScript. CSRF protection is applied to the
# obtain/refresh/logout views automatically; non-browser clients should leave
# cookie mode disabled and continue reading refresh tokens from the JSON body.


def _set_refresh_cookie(resp, token):
    """Attach the refresh-token cookie using the configured attributes."""
    resp.set_cookie(
        key=api_settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=api_settings.AUTH_COOKIE_HTTP_ONLY,
        secure=api_settings.AUTH_COOKIE_SECURE,
        samesite=api_settings.AUTH_COOKIE_SAMESITE,
        path=api_settings.AUTH_COOKIE_PATH,
        domain=api_settings.AUTH_COOKIE_DOMAIN,
        max_age=api_settings.AUTH_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(resp):
    """Delete the refresh-token cookie.

    Cookie identity is name + domain + path (per Django docs: "path and domain
    should be the same values you used in set_cookie() - otherwise the cookie
    may not be deleted"). samesite is passed so the deletion Set-Cookie header
    mirrors _set_refresh_cookie exactly (handles SameSite=None + Secure
    correctly; available since Django 2.2.15).
    """
    resp.delete_cookie(
        key=api_settings.AUTH_COOKIE_NAME,
        path=api_settings.AUTH_COOKIE_PATH,
        domain=api_settings.AUTH_COOKIE_DOMAIN,
        samesite=api_settings.AUTH_COOKIE_SAMESITE,
    )


def _request_origin(request):
    """Normalize the request Origin (or Referer) to ``"scheme://netloc"``.

    A Referer header includes a path; a raw Origin comparison against bare
    origin strings would wrongly reject ``Referer: https://app.com/login``.
    Returns None if neither header is present.
    """
    value = request.headers.get("Origin")
    if value:
        return value.rstrip("/")
    referer = request.headers.get("Referer")
    if not referer:
        return None
    parts = urlsplit(referer)
    return f"{parts.scheme}://{parts.netloc}".rstrip("/")


def _validate_origin(request):
    """Defense-in-depth origin check for cookie-bearing endpoints.

    No-op when ALLOWED_AUTH_ORIGINS is None; otherwise raises PermissionDenied
    if the request origin is not in the configured allowlist. This does not
    replace Django's CSRF Origin validation; it is an explicit second gate.
    """
    allowed = api_settings.ALLOWED_AUTH_ORIGINS
    if not allowed:
        return
    origin = _request_origin(request)
    if origin not in allowed:
        raise exceptions.PermissionDenied("Disallowed origin.")


class CookieCSRFMixin:
    """Apply Django CSRF protection only when refresh-token cookie mode is on.

    Must be FIRST in the bases tuple so its dispatch() runs before the DRF/
    GenericAPIView dispatch and wraps the entire request lifecycle. Body-only
    mode (mobile, server-to-server) authenticates via the Authorization header
    and never carries cookies, so CSRF is not a concern there.
    """

    def dispatch(self, request, *args, **kwargs):
        if api_settings.REFRESH_TOKEN_IN_COOKIE:
            return csrf_protect(super().dispatch)(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class PasswordChangeDoneView(TemplateView):
    template_name = "registration/password_change_done.html"


class PasswordChangeView(BasePasswordChangeView):
    template_name = "registration/password_change_form.html"  # Custom template
    success_url = reverse_lazy("password_change_done")  # Redirect after success

    def post(self, request):
        tokenmanager = TokenManager()
        data = request.POST.copy()
        username = getattr(request.user, tokenmanager.username_field)

        new_password1 = data.get("new_password1")
        new_password2 = data.get("new_password2")

        if new_password1 != new_password2:
            form = PasswordChangeForm(request.user, request.POST)
            form.add_error("new_password2", "The new password fields didn't match.")
            return self.render_to_response(self.get_context_data(form=form))

        try:
            tokenmanager.password_change(
                username,
                data.get("old_password"),
                new_password1,
            )
        except exceptions.AuthenticationFailed as e:
            form = PasswordChangeForm(request.user, request.POST)
            detail = getattr(e, "detail", None)
            if isinstance(detail, dict):
                for field, errors in detail.items():
                    if isinstance(errors, list):
                        for error in errors:
                            form.add_error(None, str(error))
                    else:
                        form.add_error(None, str(errors))
            elif isinstance(detail, list):
                for error in detail:
                    form.add_error(None, str(error))
            else:
                form.add_error(None, str(detail) if detail else "Password change failed.")
            return self.render_to_response(self.get_context_data(form=form))
        return HttpResponseRedirect(self.get_success_url())


class PasswordResetView(RedirectView):
    # Optional: Set whether the redirect is permanent
    permanent = False  # Set to True for a permanent redirect (301)
    # Optional: Include query strings in the redirect
    query_string = True  # Set to False to ignore query strings

    # Optional: Dynamically generate the redirect URL
    def get_redirect_url(self, *args, **kwargs):
        return f"{api_settings.REMOTE_AUTH_SERVICE_URL}/accounts/password_reset/"


class TokenObtainPairView(CookieCSRFMixin, generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        # Login CSRF: in cookie mode, a successful login establishes browser
        # auth state (the refresh cookie), so the same origin/CSRF treatment as
        # refresh/logout is required to prevent login-CSRF attacks.
        if api_settings.REFRESH_TOKEN_IN_COOKIE:
            _validate_origin(request)

        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_data = dict(TokenManager().authenticate(**serializer.validated_data))

        # In cookie mode, move the refresh token into the HttpOnly cookie and
        # remove it from the JSON body so JavaScript can never read it. The
        # body-only path (default) is unchanged: refresh is returned as JSON.
        if api_settings.REFRESH_TOKEN_IN_COOKIE and "refresh" in response_data:
            refresh = response_data.pop("refresh")
            resp = response.Response(response_data)
            _set_refresh_cookie(resp, refresh)
            return resp
        return response.Response(response_data)


class TokenRefreshView(CookieCSRFMixin, generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        # Two explicit paths so body-only behavior is byte-for-byte unchanged:
        # body mode still runs the serializer (preserving the 400-on-missing
        # contract), while cookie mode reads the HttpOnly cookie directly and
        # raises 401 if absent. Cookie mode is strictly cookie-only.
        if api_settings.REFRESH_TOKEN_IN_COOKIE:
            _validate_origin(request)
            refresh = request.COOKIES.get(api_settings.AUTH_COOKIE_NAME)
            if not refresh:
                raise exceptions.AuthenticationFailed("No refresh token provided.")
        else:
            serializer = TokenRefreshSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            refresh = serializer.validated_data["refresh"]

        response_data = dict(TokenManager().refresh(refresh=refresh))

        # When ROTATE_REFRESH_TOKENS is enabled on the auth-service, the remote
        # response contains a new "refresh". Rotate it into the cookie and drop
        # it from the body; in body mode it stays in the JSON as before.
        if api_settings.REFRESH_TOKEN_IN_COOKIE and "refresh" in response_data:
            new_refresh = response_data.pop("refresh")
            resp = response.Response(response_data)
            _set_refresh_cookie(resp, new_refresh)
            return resp
        return response.Response(response_data)


class TokenVerifyView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TokenVerifySerializer

    def post(self, request):
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokenmanager.verify(**serializer.validated_data)

        return response.Response({})


@method_decorator(ensure_csrf_cookie, "get")
class CSRFTokenView(generics.GenericAPIView):
    """Bootstrap endpoint for the CSRF cookie consumed by SPA frontends.

    A same-origin SPA calls ``GET <client>/csrf/`` to make Django emit the
    ``csrftoken`` cookie, reads it from ``document.cookie``, and submits it
    in the ``X-CSRFToken`` header on subsequent POSTs to obtain/refresh/logout
    while cookie mode is enabled. Requires ``CsrfViewMiddleware`` (the E002
    system check enforces this). See the README for cross-origin guidance.
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return response.Response({"detail": "CSRF cookie set."})


class TokenLogoutView(CookieCSRFMixin, generics.GenericAPIView):
    """Clear the refresh cookie and best-effort blacklist the token server-side.

    Idempotent: returns 200 with ``{"detail": "Logged out."}`` regardless of
    whether a refresh token was present. When ``BLACKLIST_ON_LOGOUT`` is True
    (default) and a refresh token is available, the token is POSTed to the
    auth-service blacklist endpoint. Blacklist failure (timeout, 5xx, etc.) is
    caught and logged — the cookie is still cleared. Note: blacklisting a
    refresh token does NOT invalidate an already-issued access JWT; the
    frontend must also discard its in-memory access token.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if api_settings.REFRESH_TOKEN_IN_COOKIE:
            _validate_origin(request)

        refresh = (
            request.COOKIES.get(api_settings.AUTH_COOKIE_NAME)
            if api_settings.REFRESH_TOKEN_IN_COOKIE
            else request.data.get("refresh")
        )

        if refresh and api_settings.BLACKLIST_ON_LOGOUT:
            try:
                TokenManager().blacklist(refresh)
            except exceptions.AuthenticationFailed:
                # TokenManager.__request converts every remote failure mode
                # (timeout / 5xx / bad content-type / JSON decode error) into
                # AuthenticationFailed, so this catch covers the full remote
                # error surface. The cookie is cleared regardless; a copied
                # refresh token remains valid until its natural expiry if this
                # call fails.
                logger.warning("Refresh-token blacklist failed during logout", exc_info=True)

        resp = response.Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        if api_settings.REFRESH_TOKEN_IN_COOKIE:
            _clear_refresh_cookie(resp)
        return resp
