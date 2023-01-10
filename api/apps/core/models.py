from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantAwareModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT)

    class Meta:
        abstract = True


class DeletableModel(models.Model):
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
