from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.rigs.models import ConceptDrillship, ConceptJackupRig, ConceptSemiRig

    add_staff_permissions(ConceptJackupRig, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(ConceptSemiRig, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(ConceptDrillship, ('add', 'change', 'delete', 'view'))


class RigsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rigs"

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
