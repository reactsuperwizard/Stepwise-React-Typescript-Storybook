from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.kims.models import KimsAPI, Tag, TagValue, Vessel

    add_staff_permissions(KimsAPI, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(Vessel, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(Tag, ('view',))
    add_staff_permissions(TagValue, ('view',))


class KimsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kims'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
