import datetime

import pytest
import pytz
from vcr import VCR

from apps.kims.factories import TagFactory, TagValueFactory, VesselFactory
from apps.kims.models import Tag, TagDataType, TagValue
from apps.kims.services import cast_tag_value, get_tags_sync_period, sync_vessel_tag_value, sync_vessel_tags


@pytest.mark.django_db
class TestSyncVesselTags:
    def test_should_create_vessel_tags(self, valid_kims_vessel_id: str, valid_kims_tag_id: str, request_recorder: VCR):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )

        assert Tag.objects.filter(vessel=vessel).count() == 0

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json", match_on=['host', 'path', 'method']
        ):
            sync_vessel_tags(vessel=vessel)

        assert Tag.objects.filter(vessel=vessel, deleted=False).count() == 14

        tag = Tag.objects.get(name=valid_kims_tag_id, vessel=vessel)

        assert tag.data_type == 'Double'

    @pytest.mark.parametrize('deleted', (True, False))
    def test_should_update_vessel_tags(
        self, deleted: bool, valid_kims_vessel_id: str, valid_kims_tag_id: str, request_recorder: VCR
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        tag = TagFactory(vessel=vessel, name=valid_kims_tag_id, data_type="Object", deleted=deleted)

        assert Tag.objects.filter(vessel=vessel, deleted=False).count() == int(not deleted)

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json", match_on=['host', 'path', 'method']
        ):
            sync_vessel_tags(vessel=vessel)

        assert Tag.objects.filter(vessel=vessel, deleted=False).count() == 14

        tag.refresh_from_db()

        assert tag.data_type == 'Double'
        assert tag.deleted is False

    def test_should_delete_vessel_tags(self, valid_kims_vessel_id: str, valid_kims_tag_id: str, request_recorder: VCR):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        deleted_tag = TagFactory(vessel=vessel, name='Deleted tag', deleted=False)
        unknown_tag = TagFactory(name='Unknown tag')

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json", match_on=['host', 'path', 'method']
        ):
            sync_vessel_tags(vessel=vessel)

        assert Tag.objects.filter(vessel=vessel).count() == 15
        assert Tag.objects.filter(vessel=vessel, deleted=False).count() == 14

        deleted_tag.refresh_from_db()
        unknown_tag.refresh_from_db()

        assert deleted_tag.deleted is True
        assert unknown_tag.deleted is False

    def test_should_raise_value_error_for_inactive_vessel(self):
        vessel = VesselFactory(is_active=False)

        with pytest.raises(ValueError, match="Only an active vessel can be synced with KIMS."):
            sync_vessel_tags(vessel=vessel)


@pytest.mark.django_db
class TestSyncVesselTagValue:
    @pytest.fixture
    def start(self):
        return datetime.datetime(year=2021, month=8, day=19, hour=0, tzinfo=pytz.UTC)

    @pytest.fixture
    def end(self):
        return datetime.datetime(year=2021, month=8, day=19, hour=1, tzinfo=pytz.UTC)

    def test_should_create_tag_value(
        self,
        valid_kims_vessel_id: str,
        valid_kims_tag_id: str,
        request_recorder: VCR,
        start: datetime,
        end: datetime,
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        tag = TagFactory(vessel=vessel, name=valid_kims_tag_id)

        assert TagValue.objects.filter(tag=tag).exists() is False

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.json", match_on=['host', 'path', 'method']
        ):
            sync_vessel_tag_value(tag=tag, start=start, end=end)

        tag_value = TagValue.objects.get(tag=tag)

        assert tag_value.mean == '223.598153495789'
        assert tag_value.average == '223.079283210641'
        assert tag_value.date == start

    def test_should_update_tag_value(
        self,
        valid_kims_vessel_id: str,
        valid_kims_tag_id: str,
        request_recorder: VCR,
        start: datetime,
        end: datetime,
    ):
        vessel = VesselFactory(
            kims_vessel_id=valid_kims_vessel_id,
            kims_api__base_url='https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/',
        )
        tag = TagFactory(vessel=vessel, name=valid_kims_tag_id)
        tag_value = TagValueFactory(tag=tag, mean='123.456', date=start)

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.json", match_on=['host', 'path', 'method']
        ):
            sync_vessel_tag_value(tag=tag, start=start, end=end)

        tag_value.refresh_from_db()

        assert tag_value.mean == '223.598153495789'
        assert tag_value.average == '223.079283210641'
        assert tag_value.date == start


@pytest.mark.django_db
@pytest.mark.freeze_time("2022-01-14 12:02:01")
class TestGetTagsSyncPeriod:
    @pytest.fixture()
    def start(self):
        return datetime.datetime(
            year=2022, month=1, day=14, hour=11, minute=0, second=0, microsecond=0, tzinfo=pytz.UTC
        )

    @pytest.fixture()
    def end(self):
        return datetime.datetime(
            year=2022, month=1, day=14, hour=12, minute=0, second=0, microsecond=0, tzinfo=pytz.UTC
        )

    def test_get_tags_sync_period_for_new_vessel(self, start: datetime.datetime, end: datetime.datetime):
        vessel = VesselFactory(tags_synced_at=None)

        period_start, period_end = get_tags_sync_period(vessel)

        assert period_start == start
        assert period_end == end

    def test_get_tags_sync_period_for_previously_synced_vessel(self, start: datetime.datetime, end: datetime.datetime):
        vessel = VesselFactory(tags_synced_at=start)

        period_start, period_end = get_tags_sync_period(vessel)

        assert period_start == start
        assert period_end == end

    def test_get_tags_sync_period_for_already_synced_vessel(self, start: datetime.datetime, end: datetime.datetime):
        vessel = VesselFactory(tags_synced_at=end)

        with pytest.raises(ValueError, match='Vessel tags are already synced'):
            get_tags_sync_period(vessel)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'data_type, input_value, output_value',
    (
        (TagDataType.DOUBLE, 'NaN', None),
        (TagDataType.DOUBLE, '307.288288288288', 307.288288288288),
        (TagDataType.OBJECT, 'NaN', None),
        (TagDataType.OBJECT, 'True', True),
        (TagDataType.OBJECT, 'False', False),
        (TagDataType.BOOLEAN, 'NaN', None),
        (TagDataType.BOOLEAN, '1.0', True),
        (TagDataType.BOOLEAN, '0.0', False),
        (TagDataType.SINGLE, 'NaN', None),
        (TagDataType.SINGLE, '3964.66311428712', 3964.66311428712),
        (TagDataType.INT_32, 'NaN', None),
        (TagDataType.INT_32, '256.0', 256.0),
        ('Unknown', '3964.66311428712', '3964.66311428712'),
    ),
)
def test_cast_tag_value(data_type, input_value, output_value):
    assert cast_tag_value(data_type, input_value) == output_value
