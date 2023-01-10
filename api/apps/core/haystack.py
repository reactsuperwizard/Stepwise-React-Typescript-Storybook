from celery_haystack.signals import CelerySignalProcessor
from celery_haystack.utils import get_update_task
from django.conf import settings


class SyncCelerySignalProcessor(CelerySignalProcessor):
    def run_task(self) -> None:
        options = {}
        if settings.CELERY_HAYSTACK_QUEUE:
            options['queue'] = settings.CELERY_HAYSTACK_QUEUE
        if settings.CELERY_HAYSTACK_COUNTDOWN:
            options['countdown'] = settings.CELERY_HAYSTACK_COUNTDOWN

        if self._queue:  # type: ignore
            task = get_update_task()
            task.apply((self._queue,), {}, **options)  # type: ignore

            self._queue = []  # type: ignore
