import datetime

from django.db import models
from django.utils import timezone
from django_filters import rest_framework as filters


class CustomRigListFilter(filters.FilterSet):
    draft = filters.BooleanFilter(method="filter_draft")
    latest = filters.BooleanFilter(method="filter_latest")

    def filter_latest(self, queryset: models.QuerySet, name: str, value: bool) -> models.QuerySet:
        if value:
            return queryset.filter(created_at__gte=timezone.now() - datetime.timedelta(hours=24))
        return queryset

    def filter_draft(self, queryset: models.QuerySet, name: str, value: bool) -> models.QuerySet:
        if value:
            return queryset.filter(draft=True)
        else:
            return queryset.filter(draft=False)
