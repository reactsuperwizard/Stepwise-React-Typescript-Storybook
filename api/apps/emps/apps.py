from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.emps.models import ConceptEMPElement

    add_staff_permissions(ConceptEMPElement, ('add', 'change', 'delete', 'view'))


class EmpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emps'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
