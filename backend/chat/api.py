from functools import wraps

from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework import status
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from chat import services
from chat.serializers import CredentialsSerializer
from chat.ws import ChatConnection


def _token_response(user, http_status=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=http_status,
    )


class RegisterApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_register(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "username taken"}, status=status.HTTP_400_BAD_REQUEST
            )
        return _token_response(user, status.HTTP_201_CREATED)


class LoginApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_login(**serializer.validated_data)
        if user is None:
            return Response(
                {"detail": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        return _token_response(user)


class MeApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"username": request.user.username})


class IgnoreAcceptHeader(BaseContentNegotiation):
    """Pushpin asks for application/websocket-events, which no DRF renderer
    offers; the view answers with plain HttpResponses anyway."""

    def select_parser(self, request, parsers):
        return next(iter(parsers))

    def select_renderer(self, request, renderers, format_suffix=None):
        renderer = next(iter(renderers))
        return renderer, renderer.media_type


class QueryTokenAuthentication(JWTAuthentication):
    """Browsers cannot set headers on a websocket handshake, so the JWT
    rides in the ?token= query parameter instead."""

    def authenticate(self, request):
        token = request.query_params.get("token")
        if not token:
            return None
        try:
            validated = self.get_validated_token(token.encode())
        except (InvalidToken, TokenError):
            return None
        return self.get_user(validated), validated


def require_wscontext(method):
    """Only let GRIP WebSocket-over-HTTP requests through."""

    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        if request.wscontext is None:
            return HttpResponseBadRequest("websocket only")
        return method(self, request, *args, **kwargs)

    return wrapper


class WsView(APIView):
    authentication_classes = [QueryTokenAuthentication]
    permission_classes = [AllowAny]
    # the drf stubs mistype this attribute as str | None
    content_negotiation_class = IgnoreAcceptHeader  # pyright: ignore[reportAssignmentType]

    @require_wscontext
    def post(self, request):
        if not ChatConnection(request.wscontext).process(request.user):
            return HttpResponse(status=401)
        return HttpResponse()
