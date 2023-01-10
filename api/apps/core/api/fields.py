from typing import Any, cast

from django.conf import settings
from rest_framework import serializers

from apps.core.urls import get_app_url


class FileURLField(serializers.URLField):
    def to_representation(self, value: Any) -> str:
        if not value:
            return ''
        if settings.USE_S3:
            return cast(str, value.url)
        return f'{get_app_url()}{value.url}'
