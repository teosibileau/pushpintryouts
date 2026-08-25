from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from chat.ws import ChatConnection


@csrf_exempt
def ws_view(request):
    ws = request.wscontext
    if ws is None:
        return HttpResponseBadRequest("websocket only")

    if not ChatConnection(ws).process(request.user):
        return HttpResponse(status=401)
    return HttpResponse()
