from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.emissions.models import Asset, AssetReferenceMaterial, ConceptMode, ConceptPhase

    add_staff_permissions(Asset, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(AssetReferenceMaterial, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(ConceptPhase, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(ConceptMode, ('add', 'change', 'delete', 'view'))


class EmissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emissions'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
