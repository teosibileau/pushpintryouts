from functools import wraps

from django.http import HttpResponse, HttpResponseBadRequest
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.views import APIView

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
