from django.db import models

from apps.core.models import TimestampedModel


class Notification(TimestampedModel):
    tenant_user = models.ForeignKey('tenants.TenantUserRelation', on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notification: {self.pk}'
