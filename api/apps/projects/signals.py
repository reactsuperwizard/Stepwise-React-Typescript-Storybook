from typing import Type

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from haystack import connection_router, connections
from haystack.utils import loading

from apps.projects.models import Project


def update_study_index(action: str, project: Project) -> None:
    signal_processor_class = loading.import_class(settings.HAYSTACK_SIGNAL_PROCESSOR)
    signal_processor = signal_processor_class(connections, connection_router)
    signal_processor._queue.append((action, f'studies.study.{project.pk}'))
    transaction.on_commit(signal_processor.run_task)


@receiver(post_save, sender=Project)
def post_save_project(sender: Type[Project], instance: Project, **kwargs: dict) -> None:
    # manually update search index for Study(proxy model) on Project create (ugly, but it works)
    update_study_index('update', instance)


@receiver(post_delete, sender=Project)
def post_delete_project(sender: Type[Project], instance: Project, **kwargs: dict) -> None:
    # manually update search index for Study(proxy model) on Project delete (ugly, but it works)
    update_study_index('delete', instance)
