from rest_framework import serializers


class SearchQuerySerializer(serializers.Serializer):
    query = serializers.CharField(min_length=3)


class SearchResultSerializer(serializers.Serializer):
    id = serializers.CharField()
    url = serializers.URLField()
    type = serializers.CharField()
    name = serializers.CharField()
