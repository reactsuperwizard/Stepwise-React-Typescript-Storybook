import pytest

from apps.wells.factories import WellPlannerPlannedStepFactory


class TestWellPlannerPlannedStep:
    @pytest.mark.django_db
    def test_total_duration(self):
        planned_step = WellPlannerPlannedStepFactory(duration=10, waiting_on_weather=10)

        assert planned_step.total_duration == 11
