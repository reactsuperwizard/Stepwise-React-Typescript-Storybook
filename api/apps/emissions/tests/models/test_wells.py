import pytest

from apps.emissions.factories import PlannedVesselUseFactory


class TestPlannedVesselUse:
    @pytest.mark.django_db
    def test_total_days(self):
        vessel_use = PlannedVesselUseFactory(duration=5, waiting_on_weather=15)

        assert vessel_use.total_days == 5.75
