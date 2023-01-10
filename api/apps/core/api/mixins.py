from typing import cast

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import BaseFilterBackend
from rest_framework.views import APIView

from apps.core.api.serializers import DraftSerializer


class DraftMixin(APIView):
    @property
    def is_draft(self) -> bool:
        draft_serializer = DraftSerializer(data=self.request.data)
        draft_serializer.is_valid(raise_exception=True)
        return cast(bool, draft_serializer.data['draft'])


class CustomFilterMixin(APIView):
    def custom_filter_queryset(
        self, queryset: models.QuerySet, filter_backends: list[type[BaseFilterBackend] | type[DjangoFilterBackend]]
    ) -> models.QuerySet:
        for backend in filter_backends:
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset
