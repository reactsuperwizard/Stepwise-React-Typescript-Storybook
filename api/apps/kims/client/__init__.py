import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

from django.core.cache import cache
from pydantic import ValidationError
from requests import RequestException, Session
from requests.auth import AuthBase

from ..models import KimsAPI
from .responses import CalculatedValuesData, TagsData

logger = logging.getLogger(__name__)


class KimsClientException(Exception):
    pass


class BearerTokenAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = f"Bearer {self.token}"
        return r


class KimsSession(Session):
    base_url: str

    def __init__(self, base_url: str, auth: BearerTokenAuth | None):
        super().__init__()
        self.base_url = base_url
        self.auth = auth

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        return super().request(method, url, *args, **kwargs)


class KimsClient:
    def __init__(self, username: str, password: str, base_url: str, auth: BearerTokenAuth | None = None):
        assert username
        assert password
        self.username = username
        self.password = password
        self.base_url = base_url
        self.auth = auth

    def session(self) -> KimsSession:
        return KimsSession(self.base_url, auth=self.auth)

    def authenticate(self) -> tuple[BearerTokenAuth, int]:
        logger.info('Requesting auth token')

        data = {"Username": self.username, "Password": self.password}
        with self.session() as session:
            try:
                response = session.post("token", json=data)
                response.raise_for_status()
                self.auth = BearerTokenAuth(response.json()['token'])
            except RequestException as e:
                logger.warning('Unable to authenticate in KIM-S API', exc_info=e)
                raise KimsClientException from e

        logger.info("Authenticated in KIM-S API")
        # token is valid for 30 minutes
        return self.auth, int(timedelta(minutes=30).total_seconds())

    def get_tags(self, vessel_id: str) -> TagsData:
        logger.info(f'Requesting vessel tags for Vessel({vessel_id}).')

        with self.session() as session:
            try:
                response = session.get(f"Vessels('{vessel_id}')/Tags")
                response.raise_for_status()
            except RequestException as e:
                logger.warning(f'Unable to get tags for Vessel({vessel_id}).', exc_info=e)
                raise KimsClientException from e

        try:
            return TagsData(**response.json())
        except ValidationError as e:
            logger.warning(
                f"Unable to parse tags response for Vessel({vessel_id}). Invalid response format.", exc_info=e
            )
            raise KimsClientException from e

    def get_calculated_values(
        self, *, vessel_id: str, tag_id: str, method: list[str], interval: str, start: datetime, end: datetime
    ) -> CalculatedValuesData:
        logger.info(
            f'Requesting calculated values({",".join(method)}) for Vessel({vessel_id}) and Tag({tag_id}) between {start} and {end} for {interval} interval.'
        )

        params = {
            'method': ','.join(method),
            'from': start.isoformat().replace('+00:00', 'Z'),
            'to': end.isoformat().replace('+00:00', 'Z'),
            'interval': interval,
        }

        with self.session() as session:
            try:
                response = session.get(f"Vessels('{vessel_id}')/Tags('{tag_id}')/CalculatedValues", params=params)
                response.raise_for_status()
            except RequestException as e:
                logger.warning(f'Unable to get calculated values for Vessel({vessel_id}) and Tag({tag_id})', exc_info=e)
                raise KimsClientException from e

        try:
            return CalculatedValuesData(**response.json())
        except ValidationError as e:
            logger.warning(
                f"Unable to parse calculated values for Vessel({vessel_id}) and Tag({tag_id}). Invalid response format.",
                exc_info=e,
            )
            raise KimsClientException from e


def kims_auth_token_key(api: KimsAPI) -> str:
    return f'kims-auth-token/{api.pk}'


def get_kims_client(api: KimsAPI) -> KimsClient:
    auth_key = kims_auth_token_key(api)
    cached_auth_token: str | None = cache.get(auth_key)

    kims_client = KimsClient(
        username=api.username,
        password=api.password,
        base_url=api.base_url,
        auth=BearerTokenAuth(cached_auth_token) if cached_auth_token else None,
    )
    if not cached_auth_token:
        auth_token, token_expire_time = kims_client.authenticate()
        cache.set(auth_key, auth_token.token, token_expire_time)

    return kims_client
