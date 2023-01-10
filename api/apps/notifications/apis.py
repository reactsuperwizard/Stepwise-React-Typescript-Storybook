from typing import cast

from django.db import models
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationListSerializer, UnreadNotificationsSerializer
from apps.notifications.services import read_notification, read_notifications
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser


class NotificationListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = NotificationListSerializer

    def get_queryset(self) -> models.QuerySet[Notification]:
        return Notification.objects.filter(
            tenant_user__tenant=self.tenant, tenant_user__user=cast(User, self.request.user)
        ).order_by('-created_at')

    @extend_schema(summary="Notification list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ReadNotificationsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        summary="Mark all notifications as read",
        responses={204: None},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        read_notifications(user=cast(User, self.request.user), tenant=self.tenant)
        return Response(status=204)


class UnreadNotificationsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        summary="Number of unread notifications",
        responses={200: UnreadNotificationsSerializer},
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        count = Notification.objects.filter(
            tenant_user__tenant=self.tenant,
            tenant_user__user=cast(User, self.request.user),
            read=False,
        ).count()
        return Response(UnreadNotificationsSerializer(dict(count=count)).data)


class ReadNotificationApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        summary="Mark notification as read",
        responses={204: None},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        notification = get_object_or_404(
            Notification.objects.filter(
                tenant_user__tenant=self.tenant, tenant_user__user=cast(User, self.request.user)
            ),
            pk=kwargs['notification_id'],
        )
        read_notification(user=cast(User, self.request.user), notification=notification)
        return Response(status=204)
