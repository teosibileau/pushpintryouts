from rest_framework import serializers


class CredentialsFrameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)


class MessageFrameSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)
