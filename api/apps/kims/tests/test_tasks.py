import datetime
from unittest.mock import MagicMock, call

import pytest
import pytz
from celery import states
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from pytest_mock import MockerFixture
from vcr import VCR

from apps.kims.factories import KimsAPIFactory, TagFactory, VesselFactory
from apps.kims.tasks import (
    sync_vessel_tag_value_task,
    sync_vessel_tags_task,
    sync_vessel_tags_values_task,
    sync_vessels_task,
    synced_vessel_task,
)

FREEZE_TIME = '2022-05-11'


@pytest.fixture
def start_datetime():
    return datetime.datetime(year=2021, month=8, day=19, hour=0, tzinfo=pytz.UTC).isoformat()


@pytest.fixture
def end_datetime():
    return datetime.datetime(year=2021, month=8, day=19, hour=1, tzinfo=pytz.UTC).isoformat()


@pytest.mark.django_db
class TestSyncVesselsTask:
    @pytest.fixture
    def mock_sync_vessel_tags_task(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.kims.tasks.sync_vessel_tags_task.apply_async")

    @pytest.mark.freeze_time(FREEZE_TIME)
    def test_should_sync_vessels(self, mock_sync_vessel_tags_task: MagicMock):
        start = timezone.now() - datetime.timedelta(hours=1)
        end = timezone.now()
        kims_api = KimsAPIFactory()
        unsynced_active_vessel = VesselFactory(is_active=True, tags_synced_at=None, kims_api=kims_api)
        VesselFactory(is_active=False, tags_synced_at=None)

        outdated_active_vessel = VesselFactory(
            is_active=True, tags_synced_at=timezone.now() - datetime.timedelta(hours=1), kims_api=kims_api
        )
        VesselFactory(is_active=False, tags_synced_at=timezone.now() - datetime.timedelta(hours=1))

        result = sync_vessels_task.apply()

        assert result.get() is None
        assert result.state == states.SUCCESS

        assert mock_sync_vessel_tags_task.call_count == 2
        mock_sync_vessel_tags_task.assert_has_calls(
            [
                call(
                    args=(
                        unsynced_active_vessel.kims_api_id,
                        unsynced_active_vessel.pk,
                    ),
                    countdown=0,
                    link=sync_vessel_tags_values_task.si(
                        unsynced_active_vessel.pk,
                        start.isoformat(),
                        end.isoformat(),
                    ),
                ),
                call(
                    args=(
                        outdated_active_vessel.kims_api_id,
                        outdated_active_vessel.pk,
                    ),
                    countdown=2,
                    link=sync_vessel_tags_values_task.si(
                        outdated_active_vessel.pk,
                        start.isoformat(),
                        end.isoformat(),
                    ),
                ),
            ]
        )


@pytest.mark.django_db
class TestSyncVesselTagsTask:
    def test_sync_vessel_tags(
        self,
        request_recorder: VCR,
        valid_kims_vessel_id,
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            is_active=True,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json",
            match_on=['host', 'path', 'method'],
        ):
            result = sync_vessel_tags_task.apply(
                args=(
                    vessel.kims_api_id,
                    vessel.pk,
                )
            )

        assert result.get() is True
        assert result.state == states.SUCCESS

    def test_unable_to_sync_vessel_tags(
        self,
        invalid_kims_vessel_id,
        request_recorder: VCR,
    ):
        vessel = VesselFactory(
            kims_vessel_id=invalid_kims_vessel_id,
            is_active=True,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.error.json",
            match_on=['host', 'path', 'method'],
            allow_playback_repeats=True,
        ):
            result = sync_vessel_tags_task.apply(
                args=(
                    vessel.kims_api_id,
                    vessel.pk,
                )
            )

        with pytest.raises(MaxRetriesExceededError):
            result.get()
        assert result.state == states.FAILURE

    def test_sync_inactive_vessel(
        self,
        valid_kims_vessel_id,
    ):
        vessel = VesselFactory(kims_vessel_id=valid_kims_vessel_id, is_active=False)

        result = sync_vessel_tags_task.apply(
            args=(
                vessel.kims_api_id,
                vessel.pk,
            )
        )

        assert result.get() is False
        assert result.state == states.SUCCESS


@pytest.mark.django_db
class TestSyncVesselTagsValuesTask:
    @pytest.fixture
    def mock_chord(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.kims.tasks.chord")

    def test_sync_vessel_tags_values_task(
        self, valid_kims_vessel_id: str, start_datetime: str, end_datetime: str, mock_chord: MagicMock
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            is_active=True,
        )
        tag = TagFactory(vessel=vessel)
        TagFactory(vessel=vessel, deleted=True)
        TagFactory()

        result = sync_vessel_tags_values_task.apply(args=(vessel.pk, start_datetime, end_datetime))

        assert result.get() is True
        assert result.state == states.SUCCESS

        mock_chord.assert_called_once_with(
            [
                sync_vessel_tag_value_task.si(vessel.kims_api_id, tag.pk, start_datetime, end_datetime),
            ]
        )
        mock_chord.return_value.assert_called_once_with(synced_vessel_task.si(vessel.pk, start_datetime, end_datetime))

    def test_sync_inactive_vessel(self, start_datetime: str, end_datetime: str, mock_chord: MagicMock):
        vessel = VesselFactory(
            is_active=False,
        )

        result = sync_vessel_tags_values_task.apply(args=(vessel.pk, start_datetime, end_datetime))

        assert result.get() is False
        assert result.state == states.SUCCESS

        mock_chord.assert_not_called()


@pytest.mark.django_db
class TestSyncVesselTagValueTask:
    def test_sync_vessel_tag_value_task(
        self,
        request_recorder: VCR,
        valid_kims_vessel_id: str,
        valid_kims_tag_id: str,
        start_datetime: str,
        end_datetime: str,
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            is_active=True,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        tag = TagFactory(vessel=vessel, name=valid_kims_tag_id)

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.json",
            match_on=['host', 'path', 'method'],
        ):
            result = sync_vessel_tag_value_task.apply(args=(vessel.kims_api_id, tag.pk, start_datetime, end_datetime))

        assert result.get() is True
        assert result.state == states.SUCCESS

    def test_unable_to_sync_vessel_tag_value_task(
        self,
        valid_kims_vessel_id: str,
        invalid_kims_tag_id: str,
        request_recorder: VCR,
        start_datetime: str,
        end_datetime: str,
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            is_active=True,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        tag = TagFactory(vessel=vessel, name=invalid_kims_tag_id)
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.error.json",
            match_on=['host', 'path', 'method'],
            allow_playback_repeats=True,
        ):
            result = sync_vessel_tag_value_task.apply(args=(vessel.kims_api_id, tag.pk, start_datetime, end_datetime))

        with pytest.raises(MaxRetriesExceededError):
            assert result.get() is False
        assert result.state == states.FAILURE

    def test_sync_invalid_tag(self, start_datetime: str, end_datetime: str):
        result = sync_vessel_tag_value_task.apply(args=(1, 999, start_datetime, end_datetime))

        assert result.get() is False
        assert result.state == states.SUCCESS


@pytest.mark.django_db
class TestSyncedVesselTask:
    @pytest.fixture
    def mock_sync_overlapping_monitor_functions_task(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("apps.kims.tasks.sync_overlapping_monitor_functions_task.delay")

    @pytest.mark.freeze_time(FREEZE_TIME)
    def test_synced_vessel_task(
        self, start_datetime: str, end_datetime: str, mock_sync_overlapping_monitor_functions_task
    ):
        vessel = VesselFactory(tags_synced_at=timezone.now() - datetime.timedelta(hours=1))

        result = synced_vessel_task.apply(args=(vessel.pk, start_datetime, end_datetime))

        assert result.get() is True
        assert result.state == states.SUCCESS

        vessel.refresh_from_db()

        assert vessel.tags_synced_at == datetime.datetime.fromisoformat(end_datetime).replace(tzinfo=pytz.UTC)

        mock_sync_overlapping_monitor_functions_task.assert_called_once_with(
            vessel.pk,
            start_datetime,
            (datetime.datetime.fromisoformat(end_datetime) - datetime.timedelta(hours=1)).isoformat(),
        )

    def test_synced_inactive_vessel(
        self, start_datetime: str, end_datetime: str, mock_sync_overlapping_monitor_functions_task
    ):
        vessel = VesselFactory(
            is_active=False,
        )

        result = sync_vessel_tags_values_task.apply(args=(vessel.pk, start_datetime, end_datetime))

        assert result.get() is False
        assert result.state == states.SUCCESS

        mock_sync_overlapping_monitor_functions_task.assert_not_called()
