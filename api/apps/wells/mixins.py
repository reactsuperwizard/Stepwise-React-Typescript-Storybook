from functools import cached_property
from typing import cast

from rest_framework.generics import get_object_or_404

from apps.tenants.mixins import TenantMixin
from apps.wells.models import WellPlanner, WellPlannerCompleteStep, WellPlannerPlannedStep


class WellPlannerMixin(TenantMixin):
    @cached_property
    def well_planner(self) -> WellPlanner:
        well_planner = get_object_or_404(
            WellPlanner.objects.live().filter(asset__tenant=self.tenant), pk=self.kwargs['well_planner_id']
        )
        return cast(WellPlanner, well_planner)

    @cached_property
    def complete_step(self) -> WellPlannerCompleteStep:
        return cast(
            WellPlannerCompleteStep,
            get_object_or_404(
                self.well_planner.complete_steps.all(),  # type: ignore
                pk=self.kwargs['well_planner_complete_step_id'],
            ),
        )

    @cached_property
    def planned_step(self) -> WellPlannerPlannedStep:
        return cast(
            WellPlannerPlannedStep,
            get_object_or_404(
                self.well_planner.planned_steps.all(),  # type: ignore
                pk=self.kwargs['well_planner_planned_step_id'],
            ),
        )
