import datetime
from datetime import timedelta
from unittest.mock import MagicMock, call

import pytest
from celery import states
from django.utils import timezone
from pytest_mock import MockerFixture

from apps.kims.factories import VesselFactory
from apps.kims.models import Vessel
from apps.monitors.factories import MonitorFunctionFactory
from apps.monitors.tasks import (
    sync_all_monitor_function_values_task,
    sync_monitor_function_values_task,
    sync_overlapping_monitor_functions_task,
)


@pytest.mark.django_db
class TestSyncMonitorFunctionValuesTask:
    @pytest.fixture
    def mock_sync_monitor_function_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.monitors.tasks.sync_monitor_function_values")

    def test_should_sync_monitor_function_values(self, mock_sync_monitor_function_values):
        start = timezone.now() - timedelta(days=1)
        end = timezone.now()
        monitor_function = MonitorFunctionFactory()

        result = sync_monitor_function_values_task.apply(args=(monitor_function.pk, start.isoformat(), end.isoformat()))

        assert result.get() is True
        assert result.state == states.SUCCESS
        mock_sync_monitor_function_values.assert_called_once_with(
            monitor_function=monitor_function, start_date=start, end_date=end
        )

    def test_should_not_sync_draft_monitor_function_values(self, mock_sync_monitor_function_values):
        monitor_function = MonitorFunctionFactory(draft=True)
        start = timezone.now() - timedelta(days=1)
        end = timezone.now()

        result = sync_monitor_function_values_task.apply(args=(monitor_function.pk, start.isoformat(), end.isoformat()))

        assert result.get() is False
        assert result.state == states.SUCCESS
        mock_sync_monitor_function_values.assert_not_called()


@pytest.mark.django_db
class TestSyncAllMonitorFunctionValuesTask:
    @pytest.fixture
    def mock_sync_all_monitor_function_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.monitors.tasks.sync_all_monitor_function_values")

    def test_should_sync_all_monitor_function_values(self, mock_sync_all_monitor_function_values):
        monitor_function = MonitorFunctionFactory()

        result = sync_all_monitor_function_values_task.apply(args=(monitor_function.pk,))

        assert result.get() is True
        assert result.state == states.SUCCESS
        mock_sync_all_monitor_function_values.assert_called_once_with(monitor_function)

    def test_should_not_sync_draft_monitor_function_values(self, mock_sync_all_monitor_function_values):
        monitor_function = MonitorFunctionFactory(draft=True)

        result = sync_all_monitor_function_values_task.apply(args=(monitor_function.pk,))

        assert result.get() is False
        assert result.state == states.SUCCESS
        mock_sync_all_monitor_function_values.assert_not_called()


@pytest.mark.django_db
class TestSyncOverlappingMonitorFunctionsTask:
    @pytest.fixture
    def mock_sync_monitor_function_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.monitors.tasks.sync_monitor_function_values_task.delay")

    @pytest.fixture
    def tags_synced_at(self):
        return timezone.now().replace(minute=0, second=0, microsecond=0)

    @pytest.fixture
    def vessel(self, valid_kims_vessel_id: str, tags_synced_at: datetime.datetime) -> Vessel:
        vessel = VesselFactory(kims_vessel_id=valid_kims_vessel_id, tags_synced_at=tags_synced_at)
        return vessel

    def test_should_sync_overlapping_monitor_functions(
        self, mock_sync_monitor_function_values, vessel: Vessel, tags_synced_at: datetime.datetime
    ):
        start = tags_synced_at - datetime.timedelta(days=5)
        end = tags_synced_at - datetime.timedelta(hours=1)
        MonitorFunctionFactory()
        MonitorFunctionFactory(
            draft=True,
            start_date=tags_synced_at - timedelta(days=3),
            vessel=vessel,
        )
        MonitorFunctionFactory(
            start_date=tags_synced_at + timedelta(days=1),
            vessel=vessel,
        )

        monitor_function_1 = MonitorFunctionFactory(
            start_date=tags_synced_at - timedelta(days=10),
            vessel=vessel,
        )
        monitor_function_2 = MonitorFunctionFactory(
            start_date=tags_synced_at - timedelta(days=1),
            vessel=vessel,
        )
        monitor_function_3 = MonitorFunctionFactory(
            start_date=end,
            vessel=vessel,
        )

        result = sync_overlapping_monitor_functions_task.apply(args=(vessel.pk, start.isoformat(), end.isoformat()))
        assert result.get() is None
        assert result.state == states.SUCCESS

        assert mock_sync_monitor_function_values.call_args_list == [
            call(monitor_function_1.pk, start.isoformat(), end.isoformat()),
            call(
                monitor_function_2.pk,
                monitor_function_2.start_date.isoformat(),
                end.isoformat(),
            ),
            call(monitor_function_3.pk, monitor_function_3.start_date.isoformat(), end.isoformat()),
        ]
