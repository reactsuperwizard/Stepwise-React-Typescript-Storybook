import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.kims.client import get_kims_client
from apps.kims.models import Tag, TagDataType, TagValue, Vessel

logger = logging.getLogger(__name__)


def cast_tag_value(data_type: TagDataType, value: str) -> float | bool | str | None:
    if value == 'NaN':
        return None
    match data_type:
        case TagDataType.DOUBLE:
            return float(value)
        case TagDataType.OBJECT:
            return value == "True"
        case TagDataType.BOOLEAN:
            return bool(float(value))
        case TagDataType.SINGLE:
            return float(value)
        case TagDataType.INT_32:
            return float(value)
        case _:
            logger.error(f'Unknown data type: {data_type}. Value: {value}')
            return value


def get_tags_sync_period(vessel: Vessel) -> tuple[datetime, datetime]:
    start = vessel.tags_synced_at or timezone.now() - timedelta(hours=1)
    start = start.replace(minute=0, second=0, microsecond=0)
    end = timezone.now().replace(minute=0, second=0, microsecond=0)
    if start == end:
        raise ValueError("Vessel tags are already synced")
    return start, end


@transaction.atomic
def sync_vessel_tags(*, vessel: Vessel) -> None:
    logger.info(f"Syncing tag values for Vessel(pk={vessel.pk})")

    if not vessel.is_active:
        logger.info(f"Unable to sync Vessel(pk={vessel.pk}). Vessel inactive.")
        raise ValueError("Only an active vessel can be synced with KIMS.")

    vessel_tags_data = get_kims_client(vessel.kims_api).get_tags(
        vessel.kims_vessel_id,
    )

    active_tags = []
    for tag_data in vessel_tags_data.value:
        logger.info(f"Syncing Tag({tag_data.name}).")

        tag, tag_created = Tag.objects.update_or_create(
            vessel=vessel, name=tag_data.name, defaults={"data_type": tag_data.data_type, "deleted": False}
        )

        if tag_created:
            logger.info(f"Tag(pk={tag.pk}) has been created.")
        else:
            logger.info(f"Tag(pk={tag.pk}) has been updated.")
        active_tags.append(tag.pk)

    logger.info("Synced all tags.")

    deleted_tags = Tag.objects.filter(vessel=vessel).exclude(pk__in=active_tags).update(deleted=True)

    logger.info(f"Deleted {deleted_tags} tags.")


@transaction.atomic
def sync_vessel_tag_value(*, tag: Tag, start: datetime, end: datetime) -> bool:
    logger.info(f"Syncing tag value for Tag(pk={tag.pk}) from {start} to {end}.")

    calculated_values_data = get_kims_client(tag.vessel.kims_api).get_calculated_values(
        vessel_id=tag.vessel.kims_vessel_id,
        start=start,
        end=end,
        tag_id=tag.name,
        interval='1h',
        method=TagValue.metrics,
    )

    for tag_data in calculated_values_data.value:
        values = dict()
        for tag_statistic_data in tag_data.statistics:
            method = tag_statistic_data.type.lower()
            values[method] = tag_statistic_data.value

        tag_value, tag_value_created = TagValue.objects.update_or_create(
            tag=tag,
            date=tag_data.timestamp,
            defaults=values,
        )

        if tag_value_created:
            logger.info(f"TagValue(pk={tag_value.pk}) has been created.")
        else:
            logger.info(f"TagValue(pk={tag_value.pk}) has been updated.")

    logger.info(f"Synced tag value for Tag({tag.name}).")

    return True
