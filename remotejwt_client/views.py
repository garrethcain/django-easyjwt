from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer
)
from .utils import TokenManager


class TokenObtainPairView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenObtainPairSerializer

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokens = tokenmanager.authenticate(**serializer.validated_data)

        return Response(tokens)


class TokenRefreshView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokens = tokenmanager.refresh(**serializer.validated_data)

        return Response(tokens)


class TokenVerifyView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenVerifySerializer

    def post(self, request):
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokenmanager = TokenManager()
        tokenmanager.verify(**serializer.validated_data)

        return Response({})
