from django.urls import path
from .views import TokenUserDetailView


urlpatterns = [
    path("users/<int:pk>/", TokenUserDetailView.as_view(), name="user_detail"),
]
