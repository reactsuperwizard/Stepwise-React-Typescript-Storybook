import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")

app = Celery("app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "execute_delete_account_requests": {
        "task": "apps.privacy.tasks.execute_delete_account_requests",
        "schedule": crontab(hour='*/1', minute='0'),
    },
    "sync_vessels": {
        "task": "apps.kims.tasks.sync_vessels_task",
        "schedule": crontab(minute=settings.SYNC_VESSELS_TASK_SCHEDULE_MINUTE),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
