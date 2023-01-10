from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_staff_group(sender: AppConfig, **kwargs: str) -> None:
    from apps.core.permissions import add_staff_permissions
    from apps.monitors.models import Monitor, MonitorElement, MonitorFunction

    add_staff_permissions(Monitor, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(MonitorElement, ('add', 'change', 'delete', 'view'))
    add_staff_permissions(MonitorFunction, ('add', 'change', 'delete', 'view'))


class MonitorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitors'

    def ready(self) -> None:
        post_migrate.connect(create_staff_group, sender=self)
