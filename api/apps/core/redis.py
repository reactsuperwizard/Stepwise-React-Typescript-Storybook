from django.conf import settings
from redis import Redis


def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_CACHE_LOCATION, decode_responses=True)
