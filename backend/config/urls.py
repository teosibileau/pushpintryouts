from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from chat.api import LoginApi, MeApi, RegisterApi, WsView

urlpatterns = [
    path("ws", WsView.as_view()),
    path("api/register", RegisterApi.as_view()),
    path("api/login", LoginApi.as_view()),
    path("api/refresh", TokenRefreshView.as_view()),
    path("api/me", MeApi.as_view()),
]
