from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.tenants.models import Tenant

    add_staff_permissions(Tenant, ('view',))


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
        from . import signals  # noqa
