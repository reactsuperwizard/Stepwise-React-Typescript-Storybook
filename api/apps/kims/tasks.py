import datetime
import logging
from collections import defaultdict

from billiard.exceptions import SoftTimeLimitExceeded
from celery import Task, chord
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.app.celery import app
from apps.core.celery.throttle import get_task_wait, throttle_task
from apps.kims.client import KimsClientException
from apps.kims.models import Tag, Vessel
from apps.kims.services import get_tags_sync_period, sync_vessel_tag_value, sync_vessel_tags
from apps.monitors.tasks import sync_overlapping_monitor_functions_task

logger = logging.getLogger(__name__)


@app.task(soft_time_limit=10)
def synced_vessel_task(vessel_id: int, start: str, end: str) -> bool:
    logger.info(f'Vessel(pk={vessel_id}) has been synced')

    try:
        vessel = Vessel.objects.get(pk=vessel_id, is_active=True)
    except Vessel.DoesNotExist:
        logger.exception(f'Unable to update sync time for Vessel(pk={vessel_id}). No active vessel found.')
        return False

    tags_synced_at = datetime.datetime.fromisoformat(end)
    vessel.tags_synced_at = tags_synced_at
    vessel.save()

    logger.info('Updated last sync time for tag values')

    sync_overlapping_monitor_functions_task.delay(
        vessel_id, start, (tags_synced_at - datetime.timedelta(hours=1)).isoformat()
    )

    logger.info('Started task to sync monitor_elements')

    return True


@app.task(bind=True, max_retries=5, soft_time_limit=60)
@throttle_task(settings.KIMS_API_REQUEST_RATE, key="kims_api_id")
def sync_vessel_tag_value_task(self: Task, kims_api_id: int, tag_id: str, start: str, end: str) -> bool:
    logger.info(f'Syncing value for Tag(pk={tag_id}) between {start} and {end}')

    try:
        tag = Tag.objects.filter(deleted=False).get(pk=tag_id)
    except Tag.DoesNotExist:
        logger.exception(f'Unable to sync value for Tag(pk={tag_id}). No active tag found.')
        return False

    try:
        return sync_vessel_tag_value(
            tag=tag, start=datetime.datetime.fromisoformat(start), end=datetime.datetime.fromisoformat(end)
        )
    except (KimsClientException, SoftTimeLimitExceeded) as e:
        logger.warning(f'Unable to sync tag value for Tag(pk={tag_id}).', exc_info=e)
        try:
            delay = get_task_wait(self, settings.KIMS_API_REQUEST_RATE, key=str(kims_api_id))
            raise self.retry(countdown=delay)
        except MaxRetriesExceededError:
            logger.exception(f'Unable to sync tag value for Tag(pk={tag_id}). Retry limit.')
            raise


@app.task(soft_time_limit=15)
def sync_vessel_tags_values_task(vessel_id: int, start: str, end: str) -> bool:
    logger.info(f'Syncing tags values for Vessel(pk={vessel_id}) between {start} and {end}')

    try:
        vessel = Vessel.objects.get(pk=vessel_id, is_active=True)
    except Vessel.DoesNotExist:
        logger.exception(f'Unable to sync Vessel(pk={vessel_id}). No active vessel found.')
        return False

    tags = Tag.objects.filter(vessel=vessel, deleted=False)

    tasks = [sync_vessel_tag_value_task.si(vessel.kims_api_id, tag.pk, start, end) for tag in tags]

    chord(tasks)(synced_vessel_task.si(vessel.pk, start, end))

    logger.info('Started tasks to sync tags values')

    return True


@app.task(bind=True, max_retries=5, soft_time_limit=60, retry_backoff=True)
@throttle_task(settings.KIMS_API_REQUEST_RATE, key="kims_api_id")
def sync_vessel_tags_task(self: Task, kims_api_id: int, vessel_id: int) -> bool:
    logger.info(f'Syncing tags for Vessel(pk={vessel_id})')

    try:
        vessel = Vessel.objects.get(pk=vessel_id, is_active=True)
    except Vessel.DoesNotExist:
        logger.exception(f'Unable to sync Vessel(pk={vessel_id}). No active vessel found.')
        return False

    try:
        sync_vessel_tags(
            vessel=vessel,
        )
        return True
    except (SoftTimeLimitExceeded, KimsClientException) as e:
        logger.warning(f'Unable to sync tags for Vessel(pk={vessel_id}).', exc_info=e)
        try:
            delay = get_task_wait(self, settings.KIMS_API_REQUEST_RATE, key=str(kims_api_id))
            raise self.retry(countdown=delay)
        except MaxRetriesExceededError:
            logger.exception(f'Unable to sync tags for Vessel(pk={vessel_id}). Retry limit.')
            raise


@app.task(soft_time_limit=30)
def sync_vessels_task() -> None:
    logger.info('Syncing active vessels')
    vessels = Vessel.objects.filter(is_active=True).filter(
        Q(tags_synced_at__isnull=True) | Q(tags_synced_at__lte=timezone.now())
    )

    delay: dict[int, int] = defaultdict(lambda: 0)
    for vessel in vessels:
        start, end = get_tags_sync_period(vessel)
        logger.info(f'Starting tasks to sync tags for Vessel(pk={vessel.pk}) between {start} and {end}')

        sync_vessel_tags_task.apply_async(
            args=(
                vessel.kims_api_id,
                vessel.pk,
            ),
            countdown=delay[vessel.kims_api_id],
            link=sync_vessel_tags_values_task.si(
                vessel.pk,
                start.isoformat(),
                end.isoformat(),
            ),
        )
        delay[vessel.kims_api_id] += 2

    logger.info('Started tasks for all active vessels')
