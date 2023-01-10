from rest_framework import serializers


class DraftSerializer(serializers.Serializer):
    draft = serializers.BooleanField()


class IDSerializer(serializers.Serializer):
    id = serializers.IntegerField()
