from typing import cast

from django.db import models
from django_filters import rest_framework as filters

from apps.rigs.models import (
    CustomDrillship,
    CustomDrillshipQuerySet,
    CustomJackupRig,
    CustomJackupRigQuerySet,
    CustomSemiRig,
    CustomSemiRigQuerySet,
)


class ProjectRigListFilter(filters.FilterSet):
    draft = filters.BooleanFilter()
    studiable = filters.BooleanFilter(method="filter_studiable", label="Studiable")

    def filter_studiable(self, queryset: models.QuerySet, name: str, value: bool) -> models.QuerySet:
        if not value:
            return queryset

        model = queryset.model
        if model in [CustomJackupRig, CustomSemiRig, CustomDrillship]:
            return cast(CustomJackupRigQuerySet | CustomSemiRigQuerySet | CustomDrillshipQuerySet, queryset).studiable()
        raise NotImplementedError(f'Unsupported filter for {model.__name__}')
