from django.urls import path, include
from .views import TokenUserDetailView


urlpatterns = [
    path(
        "user/",
        include(
            [
                path("", TokenUserDetailView.as_view(), name="user_detail"),
            ]
        ),
    ),
]
