from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'title', 'url', 'read', 'created_at')
        model = Notification


class UnreadNotificationsSerializer(serializers.Serializer):
    count = serializers.IntegerField()
