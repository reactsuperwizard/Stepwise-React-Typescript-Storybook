from datetime import datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.kims.factories import TagFactory, TagValueFactory, VesselFactory
from apps.kims.models import Vessel
from apps.monitors.factories import MonitorFunctionFactory, MonitorFunctionValueFactory
from apps.monitors.models import MonitorFunctionValue
from apps.monitors.services import (
    MonitorFunctionTestResult,
    TagDict,
    TagNotFoundException,
    _restricted_getitem,
    compile_monitor_function,
    run_monitor_function_test,
    sync_all_monitor_function_values,
    sync_monitor_function_values,
)

VALID_FUNCTION = """
def monitor(tags):
    if tags['tag-1']['mean'] is None or tags['tag-2']['mean'] is None:
        return 0

    return (tags['tag-1']['mean'] + tags['tag-2']['mean'])*2
"""

RETURN_TAG_1_FUNCTION = """
def monitor(tags):
    return tags['tag-1']['mean']
"""

INVALID_FUNCTION_TAG_NOT_FOUND = """
def monitor(tags):
    return tags['non-existing-tag']['mean']
"""

INVALID_FUNCTION_NAME = """
def invalid_function_name(tags):
    return tags['tag-1']['mean'] + tags['tag-2']['mean']
"""

INVALID_FUNCTION_RAISE_EXCEPTION = """
def monitor(tags):
    raise Exception('test-exception')
"""

INVALID_FUNCTION_SYNTAX_ERROR = """
def monitor()
    return tags['tag-1']['mean'] + tags['tag-2']['mean']
"""

INVALID_FUNCTION_RESTRICTED = """
def monitor(tags):
    import requests
    requests.get('https://google.com')
"""


@pytest.fixture
def last_sync() -> datetime:
    return timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


@pytest.mark.django_db
class TestTagDict:
    def test_should_raise_tag_not_found_instead_of_key_error(self):
        tag_dict = TagDict({})

        with pytest.raises(TagNotFoundException, match='some-tag'):
            tag_dict['some-tag']


@pytest.mark.django_db
class TestRestrictedGetItem:
    def test_should_get_item_from_tag_dict(self):
        tag_dict = TagDict({"some-tag": 1000.0})
        value = _restricted_getitem(tag_dict, 'some-tag')

        assert value == 1000.0

    @pytest.mark.parametrize('obj', ({'some-tag': 1000.0}, []))
    def test_should_raise_name_error_for_others(self, obj: dict | list):
        with pytest.raises(NameError, match='Unknown "some-tag" property used'):
            _restricted_getitem(obj, 'some-tag')


@pytest.mark.django_db
class TestCompileMonitorFunction:
    @pytest.mark.parametrize(
        'tag_dict,expected_result',
        (
            (TagDict({'tag-1': TagDict(mean=5), 'tag-2': TagDict(mean=6)}), 22),
            (TagDict({'tag-1': TagDict(mean=-10), 'tag-2': TagDict(mean=50)}), 80),
        ),
    )
    def test_should_compile_function(self, tag_dict: TagDict, expected_result: int):
        monitor_function = compile_monitor_function(monitor_function_source=VALID_FUNCTION)
        assert monitor_function(tag_dict) == expected_result

    def test_should_raise_validation_error_for_invalid_syntax(self):
        with pytest.raises(ValidationError) as ex:
            compile_monitor_function(monitor_function_source=INVALID_FUNCTION_SYNTAX_ERROR)

        assert ex.value.messages == ["Line 2: SyntaxError: expected ':' at statement: 'def monitor()'"]

    def test_monitor_function_should_raise_name_error_for_restricted_code(self):
        monitor_function = compile_monitor_function(monitor_function_source=INVALID_FUNCTION_RESTRICTED)

        with pytest.raises(NameError, match="name '_getattr_' is not defined"):
            monitor_function({})

    def test_should_raise_validation_error_for_invalid_name(self):
        with pytest.raises(ValidationError) as ex:
            compile_monitor_function(monitor_function_source=INVALID_FUNCTION_NAME)

        assert ex.value.messages == ["'monitor' function not found. Make sure to define a function called 'monitor'."]


@pytest.mark.django_db
class TestRunMonitorFunctionTest:
    @pytest.fixture
    def vessel(self, last_sync: datetime) -> Vessel:
        vessel = VesselFactory()

        tag_1 = TagFactory(name='tag-1', vessel=vessel)
        tag_2 = TagFactory(name='tag-2', vessel=vessel)
        TagValueFactory(tag=tag_1, date=last_sync, mean='1.0', average='0.0')
        TagValueFactory(date=last_sync, mean='1.0', average='0.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=2), mean='11.0', average='10.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=3), mean='11.0', average='10.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=4), mean='111.0', average='110.0')
        TagValueFactory(tag=tag_2, date=last_sync, mean='2.0', average='1.0')
        TagValueFactory(date=last_sync, mean='2.0', average='1.0')
        TagValueFactory(tag=tag_2, date=last_sync - timedelta(hours=3), mean='22.0', average='21.0')
        TagValueFactory(tag=tag_2, date=last_sync - timedelta(hours=4), mean='222.0', average='221.0')
        return vessel

    def test_should_run_monitor_function_test(self, vessel: Vessel, last_sync: datetime):
        monitor_function = compile_monitor_function(VALID_FUNCTION)

        expected_result = MonitorFunctionTestResult(
            columns=['Date', 'Result', 'tag-1', 'tag-2'],
            rows=[
                [last_sync, 6.0, dict(mean=1.0, average=0.0), dict(mean=2.0, average=1.0)],
                [last_sync - timedelta(hours=2), 0, dict(mean=11.0, average=10.0), dict(mean=None, average=None)],
                [last_sync - timedelta(hours=3), 66.0, dict(mean=11.0, average=10.0), dict(mean=22.0, average=21.0)],
            ],
        )

        assert (
            run_monitor_function_test(callable_monitor_function=monitor_function, vessel=vessel, hours=3)
            == expected_result
        )

    def test_should_raise_validation_error_for_any_exception(self, vessel: Vessel):
        callable_monitor_function = compile_monitor_function(INVALID_FUNCTION_RAISE_EXCEPTION)

        with pytest.raises(ValidationError) as ex:
            run_monitor_function_test(callable_monitor_function=callable_monitor_function, vessel=vessel, hours=3)

        assert ex.value.messages == ["test-exception"]

    def test_should_raise_validation_error_for_tag_not_found(self, vessel: Vessel):
        callable_monitor_function = compile_monitor_function(INVALID_FUNCTION_TAG_NOT_FOUND)

        with pytest.raises(ValidationError) as ex:
            run_monitor_function_test(callable_monitor_function=callable_monitor_function, vessel=vessel, hours=3)

        assert ex.value.messages == ["Tag 'non-existing-tag' not found. Available tags: tag-1, tag-2."]


@pytest.mark.django_db
class TestSyncMonitorFunctionValues:
    @pytest.fixture
    def vessel(self, last_sync: datetime) -> Vessel:
        vessel = VesselFactory(tags_synced_at=last_sync + timedelta(hours=1))

        tag_1 = TagFactory(name='tag-1', vessel=vessel)
        TagValueFactory(tag=tag_1, date=last_sync, mean='1.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=2), mean='11.0')
        TagValueFactory(date=last_sync - timedelta(hours=2), mean='33.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=3), mean='111.0')
        TagValueFactory(tag=tag_1, date=last_sync - timedelta(hours=4), mean='1111.0')
        return vessel

    def test_should_calculate_monitor_function_values_for_a_single_day(self, vessel: Vessel, last_sync: datetime):
        monitor_function = MonitorFunctionFactory(
            monitor_function_source=RETURN_TAG_1_FUNCTION,
            start_date=last_sync - timedelta(hours=2),
            vessel=vessel,
        )

        sync_monitor_function_values(
            monitor_function=monitor_function,
            start_date=last_sync - timedelta(hours=2),
            end_date=last_sync - timedelta(hours=2),
        )

        monitor_function_value = MonitorFunctionValue.objects.get(monitor_function=monitor_function)

        assert monitor_function_value.monitor_function == monitor_function
        assert monitor_function_value.value == 11.0
        assert monitor_function_value.date == last_sync - timedelta(hours=2)

    def test_should_calculate_all_monitor_function_values(self, vessel: Vessel, last_sync: datetime):
        two_hours_ago = last_sync - timedelta(hours=2)
        hour_ago = last_sync - timedelta(hours=1)
        last_day = last_sync

        monitor_function = MonitorFunctionFactory(
            monitor_function_source=RETURN_TAG_1_FUNCTION,
            start_date=two_hours_ago,
            vessel=vessel,
        )

        sync_monitor_function_values(monitor_function=monitor_function, start_date=two_hours_ago, end_date=last_day)

        first_function_value, second_function_value, third_function_value = MonitorFunctionValue.objects.all().order_by(
            'date'
        )

        assert first_function_value.monitor_function == monitor_function
        assert first_function_value.value == 11.0
        assert first_function_value.date == two_hours_ago

        assert second_function_value.monitor_function == monitor_function
        assert second_function_value.value == 0.0
        assert second_function_value.date == hour_ago

        assert third_function_value.monitor_function == monitor_function
        assert third_function_value.value == 1.0
        assert third_function_value.date == last_day

    def test_should_calculate_partial_function_values(self, vessel: Vessel, last_sync: datetime):
        monitor_function = MonitorFunctionFactory(
            start_date=last_sync - timedelta(hours=3),
            vessel=vessel,
            monitor_function_source=RETURN_TAG_1_FUNCTION,
        )
        monitor_function_value_1 = MonitorFunctionValueFactory(
            monitor_function=monitor_function,
            date=last_sync - timedelta(hours=3),
            value=9999,
        )
        monitor_function_value_2 = MonitorFunctionValueFactory(
            monitor_function=monitor_function,
            date=last_sync - timedelta(hours=2),
            value=111.0,
        )
        monitor_function_value_3 = MonitorFunctionValueFactory(
            monitor_function=monitor_function,
            date=last_sync - timedelta(hours=1),
            value=11.0,
        )
        monitor_function_value_4 = MonitorFunctionValueFactory(
            monitor_function=monitor_function,
            date=last_sync,
            value=1.0,
        )

        sync_monitor_function_values(
            monitor_function=monitor_function, start_date=last_sync - timedelta(hours=2), end_date=last_sync
        )

        monitor_function_value_1.refresh_from_db()
        monitor_function_value_2.refresh_from_db()
        monitor_function_value_3.refresh_from_db()
        monitor_function_value_4.refresh_from_db()

        assert monitor_function_value_1.monitor_function == monitor_function
        assert monitor_function_value_1.value == 9999
        assert monitor_function_value_1.date == last_sync - timedelta(hours=3)

        assert monitor_function_value_2.monitor_function == monitor_function
        assert monitor_function_value_2.value == 11.0
        assert monitor_function_value_2.date == last_sync - timedelta(hours=2)

        assert monitor_function_value_3.monitor_function == monitor_function
        assert monitor_function_value_3.value == 0
        assert monitor_function_value_3.date == last_sync - timedelta(hours=1)

        assert monitor_function_value_4.monitor_function == monitor_function
        assert monitor_function_value_4.value == 1.0
        assert monitor_function_value_4.date == last_sync

    @pytest.mark.parametrize(
        'start_date,end_date,reason',
        (
            (timezone.now() - timedelta(days=10), timezone.now(), 'start date before monitor function start date'),
            (timezone.now() - timedelta(days=1), timezone.now() + timedelta(hours=1), 'end date in the future'),
            (timezone.now() + timedelta(hours=1), timezone.now(), 'start date after end date'),
        ),
    )
    def test_should_raise_value_error_for_invalid_time_range(
        self, start_date: datetime, end_date: datetime, reason: str
    ):
        monitor_function = MonitorFunctionFactory(start_date=timezone.now() - timedelta(days=5))
        with pytest.raises(ValueError):
            sync_monitor_function_values(
                monitor_function=monitor_function,
                start_date=start_date,
                end_date=end_date,
            )


@pytest.mark.django_db
class TestSyncAllMonitorFunctionValues:
    def test_should_calculate_all_monitor_values(self, last_sync: datetime):
        monitor_function = MonitorFunctionFactory(
            start_date=last_sync, vessel__tags_synced_at=last_sync + timedelta(hours=1)
        )
        monitor_function_value_1 = MonitorFunctionValueFactory(
            monitor_function=monitor_function,
            date=last_sync - timedelta(hours=2),
        )
        monitor_function_value_2 = MonitorFunctionValueFactory(
            monitor_function=monitor_function, date=last_sync, value=999
        )

        assert sync_all_monitor_function_values(monitor_function)

        with pytest.raises(MonitorFunctionValue.DoesNotExist):
            monitor_function_value_1.refresh_from_db()

        monitor_function_value_2.refresh_from_db()

        assert monitor_function_value_2.value == 0
        assert monitor_function_value_2.date == last_sync

    def test_should_not_calculate_if_no_tags(self, last_sync: datetime):
        monitor_function = MonitorFunctionFactory(start_date=last_sync, vessel__tags_synced_at=None)

        assert sync_all_monitor_function_values(monitor_function) is False
