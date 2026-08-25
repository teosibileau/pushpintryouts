from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat import services
from chat.serializers import CredentialsSerializer


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
