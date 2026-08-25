from django.urls import path

from chat.apis import login_api, logout_api, me_api, register_api
from chat.views import WsView

urlpatterns = [
    path("ws", WsView.as_view()),
    path("api/register", register_api),
    path("api/login", login_api),
    path("api/logout", logout_api),
    path("api/me", me_api),
]
