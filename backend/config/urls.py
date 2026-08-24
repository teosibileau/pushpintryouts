from django.urls import path

from chat.views import ws_view

urlpatterns = [
    path("ws", ws_view),
]
