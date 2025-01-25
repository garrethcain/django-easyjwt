from django.urls import path
from .views import TokenUserDetailView


urlpatterns = [
    path("user/", TokenUserDetailView.as_view(), name="user_detail"),
]
