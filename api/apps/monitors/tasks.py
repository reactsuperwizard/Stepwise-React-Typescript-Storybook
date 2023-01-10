import logging
from datetime import datetime

from apps.app.celery import app
from apps.monitors.models import MonitorFunction
from apps.monitors.services import sync_all_monitor_function_values, sync_monitor_function_values

logger = logging.getLogger(__name__)


@app.task
def sync_monitor_function_values_task(monitor_function_id: int, start: str, end: str) -> bool:
    logger.info(
        f"Syncing MonitorFunction(pk={monitor_function_id}, draft=False) values between {start} and {end} in the background."
    )

    try:
        monitor_function = MonitorFunction.objects.get(pk=monitor_function_id, draft=False)
    except MonitorFunction.DoesNotExist:
        logger.exception(
            f"Unable to sync MonitorFunction(pk={monitor_function_id}, draft=False) values between {start} and {end}. MonitorFunction does not exist."
        )
        return False

    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)

    sync_monitor_function_values(
        monitor_function=monitor_function,
        start_date=start_date,
        end_date=end_date,
    )

    logger.info('Synced monitor function values')

    return True


@app.task
def sync_all_monitor_function_values_task(monitor_function_id: int) -> bool:
    logger.info(f"Syncing all MonitorFunction(pk={monitor_function_id}, draft=False) values in the background.")

    try:
        monitor_function = MonitorFunction.objects.get(pk=monitor_function_id, draft=False)
    except MonitorFunction.DoesNotExist:
        logger.exception(
            f"Unable to sync MonitorFunction(pk={monitor_function_id}, draft=False) values. MonitorFunction does not exist."
        )
        return False

    sync_all_monitor_function_values(monitor_function)

    logger.info('Synced all monitor function values')

    return True


@app.task
def sync_overlapping_monitor_functions_task(vessel_id: int, start: str, end: str) -> None:
    logger.info(
        f"Syncing monitor function values for Vessel(pk={vessel_id}) between {start} and {end} in the background."
    )

    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)

    monitor_functions = MonitorFunction.objects.filter(
        vessel_id=vessel_id,
        start_date__lte=end_date,
        draft=False,
    )

    for monitor_function in monitor_functions:
        sync_start_date = max(start_date, monitor_function.start_date)
        sync_end_date = end_date

        sync_monitor_function_values_task.delay(
            monitor_function.pk,
            sync_start_date.isoformat(),
            sync_end_date.isoformat(),
        )

        logger.info(f'Scheduled task to sync monitor function values for MonitorFunction(pk={monitor_function.pk})')
