from django.urls import path

from apps.notifications import apis

app_name = 'notifications'

urlpatterns = [
    path('notifications/', apis.NotificationListApi.as_view(), name='notification_list'),
    path('notifications/read/', apis.ReadNotificationsApi.as_view(), name='read_notifications'),
    path('notifications/unread/', apis.UnreadNotificationsApi.as_view(), name='unread_notifications'),
    path('notifications/<int:notification_id>/read/', apis.ReadNotificationApi.as_view(), name='read_notification'),
]
