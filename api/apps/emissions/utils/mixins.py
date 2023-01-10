from typing import cast

from django.utils.functional import cached_property
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView

from apps.emissions.models import Asset, Baseline
from apps.emissions.models.assets import EmissionManagementPlan
from apps.tenants.mixins import TenantMixin


class AssetMixin(TenantMixin, APIView):
    @cached_property
    def asset(self) -> Asset:
        return cast(Asset, get_object_or_404(self.tenant.asset_set.live(), pk=self.kwargs["asset_id"]))


class BaselineMixin(AssetMixin, APIView):
    @cached_property
    def baseline(self) -> Baseline:
        return cast(
            Baseline,
            get_object_or_404(self.asset.baselines.live().filter(asset=self.asset), pk=self.kwargs['baseline_id']),
        )


class EmissionManagementPlanMixin(BaselineMixin, APIView):
    @cached_property
    def emission_management_plan(self) -> EmissionManagementPlan:
        return cast(
            EmissionManagementPlan,
            get_object_or_404(
                self.baseline.emission_management_plans.live(),
                pk=self.kwargs['emission_management_plan_id'],
            ),
        )
