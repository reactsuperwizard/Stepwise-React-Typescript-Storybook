import datetime
import itertools
import logging
from datetime import timedelta
from typing import Any, Callable, TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from RestrictedPython import compile_restricted

from apps.kims.models import Tag, TagValue, Vessel
from apps.kims.services import cast_tag_value
from apps.monitors.models import MonitorFunction, MonitorFunctionValue

CallableMonitorFunction = Callable[[dict], Any]

logger = logging.getLogger(__name__)


class TagNotFoundException(KeyError):
    pass


class TagDict(dict):
    def __getitem__(self, key: str) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            raise TagNotFoundException(key)


class MonitorFunctionTestResult(TypedDict):
    columns: list[str]
    rows: list[list]


def _restricted_getitem(tags: TagDict, key: str) -> Any:
    if not isinstance(tags, TagDict):
        raise NameError(f'Unknown "{key}" property used')

    return tags[key]


def compile_monitor_function(monitor_function_source: str) -> CallableMonitorFunction:
    logger.info("Compiling monitor function")

    try:
        locals_dict = {
            '_getitem_': _restricted_getitem,
        }
        byte_code = compile_restricted(monitor_function_source, filename='<inline code>', mode='exec')
        exec(byte_code, locals_dict)

        monitor_function = locals_dict.get('monitor')
    except SyntaxError as e:
        logger.info("Unable to compile function. Error: %s", e)
        raise ValidationError({'monitor_function_source': e.msg[0]})
    except Exception as e:
        logger.info("Unable to compile function. Error %s", e)
        raise ValidationError({"monitor_function_source": f"Unable to compile function. Error: {str(e)}"})

    if not monitor_function:
        raise ValidationError(
            {
                'monitor_function_source': "'monitor' function not found. Make sure to define a function called 'monitor'."
            }
        )

    return monitor_function  # type: ignore


def generate_function_input(tag_names: list[str], tag_values: list[TagValue]) -> dict:
    function_input = TagDict.fromkeys(tag_names, TagDict(**{value: None for value in TagValue.metrics}))
    for tag_value in tag_values:
        function_input[tag_value.name] = TagDict(  # type: ignore
            **{
                value: cast_tag_value(tag_value.data_type, getattr(tag_value, value)) for value in TagValue.metrics  # type: ignore
            }
        )
    return function_input


def run_monitor_function_test(
    *, vessel: Vessel, callable_monitor_function: CallableMonitorFunction, hours: int
) -> MonitorFunctionTestResult:
    logger.info(f'Running tests for monitor function for Vessel(pk={vessel.pk}) for last {hours} hours.')
    last_sync_date = timezone.now().replace(minute=0, second=0, microsecond=0) - datetime.timedelta(hours=1)
    grouped_tag_values = (
        TagValue.objects.filter(
            tag__vessel=vessel,
            date__gte=(last_sync_date - timedelta(hours=hours)),
        )
        .with_data_type()  # type: ignore
        .with_name()
        .order_by('-date')
    )
    unique_tag_names = Tag.objects.filter(vessel=vessel).values_list('name', flat=True).order_by('name')

    columns = [
        'Date',
        'Result',
        *unique_tag_names,
    ]
    monitor_function_test_result = MonitorFunctionTestResult(columns=columns, rows=[])

    for date, grouped_tag_values in itertools.groupby(grouped_tag_values, lambda o: o.date):  # type: ignore
        test_input = generate_function_input(list(unique_tag_names), grouped_tag_values)

        try:
            result = callable_monitor_function(test_input)
        except TagNotFoundException as e:
            logger.info("Monitor function test failed. Tag %s not found.", e)
            raise ValidationError(
                {'monitor_function_source': f"Tag {e} not found. Available tags: {', '.join(unique_tag_names)}."}
            )

        except Exception as e:
            logger.exception("Monitor function test failed. Error %s", e)
            raise ValidationError({'monitor_function_source': e})

        row_tag_values = [test_input.get(tag_name, None) for tag_name in unique_tag_names]
        row = [date, result, *row_tag_values]

        monitor_function_test_result['rows'].append(row)

    logger.info('Test run for monitor function successful.')
    return monitor_function_test_result


def calculate_monitor_function_value(monitor_function: MonitorFunction, date: datetime.datetime) -> float:
    logger.info(f"Calculating value for MonitorFunction(pk={monitor_function.pk}) for {date}.")
    callable_monitor_function = compile_monitor_function(monitor_function.monitor_function_source)

    vessel = monitor_function.vessel
    unique_tag_names = Tag.objects.filter(vessel=vessel).values_list('name', flat=True)
    tag_values = (
        TagValue.objects.filter(
            tag__vessel=vessel,
            date=date,
        )
        .with_data_type()  # type: ignore
        .with_name()
    )

    monitor_function_input = generate_function_input(list(unique_tag_names), tag_values)
    logger.info('Monitor function input: %s', monitor_function_input)

    try:
        value = callable_monitor_function(monitor_function_input)
    except Exception:
        logger.exception(
            f'Unable to calculate function value for MonitorFunction(pk={monitor_function.pk}) for {date}. Returning 0. Input values: %s',
            monitor_function_input,
        )
        return 0

    return value or 0


@transaction.atomic
def sync_monitor_function_values(
    *, monitor_function: MonitorFunction, start_date: datetime.datetime, end_date: datetime.datetime
) -> None:
    logger.info(f"Calculating values for MonitorFunction(pk={monitor_function.pk}) from {start_date} to {end_date}.")
    if start_date < monitor_function.start_date:
        raise ValueError(
            "Unable to calculate monitor function values. Start date must be greater than monitor function start date."
        )
    if end_date > timezone.now():
        raise ValueError("Unable to calculate monitor function values. End date must be in the past.")
    if end_date < start_date:
        raise ValueError("Unable to calculate monitor function values. End date must come after start date.")

    current_date = start_date

    while current_date <= end_date:
        value = calculate_monitor_function_value(monitor_function, current_date)

        try:
            float(value)
        except TypeError:
            logger.exception(
                f"Expected number but got {value} as calculated value for MonitorFunction(pk={monitor_function.pk}) on {current_date}."
            )
            value = 0.0

        monitor_function_value, created = MonitorFunctionValue.objects.update_or_create(
            monitor_function=monitor_function,
            date=current_date,
            defaults={
                'value': value,
            },
        )

        if created:
            logger.info(f"Created MonitorFunctionValue(pk={monitor_function_value.pk}).")
        else:
            logger.info(f"Updated MonitorFunctionValue(pk={monitor_function_value.pk}).")

        current_date += timedelta(hours=1)

    logger.info(f"Calculated values for MonitorFunction(pk={monitor_function.pk}) from {start_date} to {end_date}.")


@transaction.atomic
def sync_all_monitor_function_values(monitor_function: MonitorFunction) -> bool:
    logger.info(f"Calculating all values for MonitorFunction(pk={monitor_function.pk}).")

    if not monitor_function.vessel.tags_synced_at:
        logger.info("No need to sync monitor function values. No synced tags.")
        return False

    monitor_function_values_to_delete = MonitorFunctionValue.objects.filter(Q(date__lt=monitor_function.start_date))

    for monitor_function_value in monitor_function_values_to_delete:
        logger.info(f"Removing MonitorFunctionValue(pk={monitor_function_value.pk}). Out of monitoring time range.")
        monitor_function_value.delete()

    sync_monitor_function_values(
        monitor_function=monitor_function,
        start_date=monitor_function.start_date,
        end_date=monitor_function.vessel.tags_synced_at - datetime.timedelta(hours=1),
    )

    return True
