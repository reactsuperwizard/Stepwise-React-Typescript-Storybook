from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant_user', 'title', 'read')
    search_fields = ('id', 'title')
    list_filter = ('read', 'created_at', 'updated_at')
    autocomplete_fields = ('tenant_user',)
