from datetime import datetime

import pytest
from django.core.cache import cache
from requests import HTTPError
from vcr import VCR

from apps.core.redis import get_redis_client
from apps.kims.client import KimsClient, KimsClientException, get_kims_client, kims_auth_token_key
from apps.kims.factories import KimsAPIFactory


@pytest.mark.django_db
class TestKimsClient:
    @pytest.fixture
    def kims_client(self, request_recorder: VCR):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json", match_on=['host', 'path', 'method']
        ):
            return KimsClient(
                username="username",
                password="password",
                base_url="https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/",
            )

    def test_should_authenticate(self, kims_client: KimsClient, request_recorder: VCR, valid_kims_vessel_id: str):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.authenticate.json", match_on=['host', 'path', 'method']
        ):
            assert kims_client.auth is None

            kims_client.authenticate()

            assert kims_client.auth.token is not None

    def test_should_fail_to_authenticate(
        self, kims_client: KimsClient, request_recorder: VCR, valid_kims_vessel_id: str
    ):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.authenticate.error.json", match_on=['host', 'path', 'method']
        ):
            with pytest.raises(KimsClientException) as ex:
                kims_client.authenticate()

            assert type(ex.value.__cause__) is HTTPError

    def test_should_get_tags(self, kims_client: KimsClient, request_recorder: VCR, valid_kims_vessel_id: str):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.json", match_on=['host', 'path', 'method']
        ):
            assert kims_client.get_tags(
                valid_kims_vessel_id,
            )

    def test_should_fail_to_get_tags(
        self,
        kims_client: KimsClient,
        request_recorder: VCR,
        invalid_kims_vessel_id: str,
    ):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_tags.error.json", match_on=['host', 'path', 'method']
        ):
            with pytest.raises(KimsClientException) as ex:
                kims_client.get_tags(
                    invalid_kims_vessel_id,
                )

        assert type(ex.value.__cause__) is HTTPError

    def test_should_get_calculated_values(
        self, kims_client: KimsClient, request_recorder: VCR, valid_kims_vessel_id: str, valid_kims_tag_id: str
    ):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.json", match_on=['host', 'path', 'method']
        ):
            assert kims_client.get_calculated_values(
                vessel_id=valid_kims_vessel_id,
                tag_id=valid_kims_tag_id,
                method=["mean"],
                interval="1h",
                start=datetime(2021, 8, 1),
                end=datetime(2021, 8, 2),
            )

    def test_should_fail_to_get_calculated_values(
        self, kims_client: KimsClient, request_recorder: VCR, valid_kims_vessel_id: str, invalid_kims_tag_id: str
    ):
        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.get_calculated_values.error.json", match_on=['host', 'path', 'method']
        ):
            with pytest.raises(KimsClientException) as ex:
                kims_client.get_calculated_values(
                    vessel_id=valid_kims_vessel_id,
                    tag_id=invalid_kims_tag_id,
                    method=["mean"],
                    interval="1h",
                    start=datetime(2021, 8, 1),
                    end=datetime(2021, 8, 2),
                )

        assert type(ex.value.__cause__) is HTTPError


@pytest.mark.django_db
class TestGetKimsClient:
    @pytest.fixture
    def token(self):
        return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NTY5NDY5NzIsImlzcyI6ImxvY2FsaG9zdCIsImF1ZCI6ImxvY2FsaG9zdCJ9.XHGASFicW5_UA_ldurK35fb65aMXf9i_E6O-ZeYwUEU'

    def test_generate_new_auth_token(self, token: str, request_recorder: VCR):
        api = KimsAPIFactory(
            base_url="https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/",
        )
        auth_key = kims_auth_token_key(api)

        with request_recorder.use_cassette(
            "kims/tests/casettes/test_client.authenticate.json", match_on=['host', 'path', 'method']
        ):
            kims_client = get_kims_client(api)

        assert kims_client.auth.token == token

        assert cache.get(kims_auth_token_key(api)) == token
        assert get_redis_client().ttl(cache.make_and_validate_key(auth_key)) == 1800

    def test_use_cached_auth_token(self, token: str, request_recorder: VCR):
        api = KimsAPIFactory(
            base_url="https://kimsapi.demo.kognif.ai/Routing/KIMSAPI/",
        )
        auth_key = kims_auth_token_key(api)
        cache.set(auth_key, token, 30 * 60)

        kims_client = get_kims_client(api)

        assert kims_client.auth.token == token
