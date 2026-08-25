from django.urls import path

from chat.apis import LoginApi, LogoutApi, MeApi, RegisterApi
from chat.views import WsView

urlpatterns = [
    path("ws", WsView.as_view()),
    path("api/register", RegisterApi.as_view()),
    path("api/login", LoginApi.as_view()),
    path("api/logout", LogoutApi.as_view()),
    path("api/me", MeApi.as_view()),
]
