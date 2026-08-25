from functools import wraps

from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework import status
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.response import Response
from rest_framework.views import APIView

from chat import services
from chat.serializers import CredentialsSerializer
from chat.ws import ChatConnection


class IgnoreAcceptHeader(BaseContentNegotiation):
    """Pushpin asks for application/websocket-events, which no DRF renderer
    offers; the view answers with plain HttpResponses anyway."""

    def select_parser(self, request, parsers):
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


def require_wscontext(method):
    """Only let GRIP WebSocket-over-HTTP requests through."""

    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        if request.wscontext is None:
            return HttpResponseBadRequest("websocket only")
        return method(self, request, *args, **kwargs)

    return wrapper


class WsView(APIView):
    content_negotiation_class = IgnoreAcceptHeader

    @require_wscontext
    def post(self, request):
        if not ChatConnection(request.wscontext).process(request.user):
            return HttpResponse(status=401)
        return HttpResponse()


class RegisterApi(APIView):
    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_register(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "username taken"}, status=status.HTTP_400_BAD_REQUEST
            )
        login(request, user)
        return Response({"username": user.username}, status=status.HTTP_201_CREATED)


class LoginApi(APIView):
    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_login(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        login(request, user)
        return Response({"username": user.username})


class LogoutApi(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeApi(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "not authenticated"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response({"username": request.user.username})
