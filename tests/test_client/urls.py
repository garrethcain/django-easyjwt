from django.urls import path, include

urlpatterns = [
    path("auth/", include("easyjwt_client.urls")),
    path("auth/", include("easyjwt_user.urls")),
]
