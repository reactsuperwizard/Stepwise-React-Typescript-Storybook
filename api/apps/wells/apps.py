from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.wells.models import ConceptWell, WellReferenceMaterial

    add_staff_permissions(ConceptWell, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(WellReferenceMaterial, ('add', 'change', 'delete', 'view'))


class WellsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wells'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
