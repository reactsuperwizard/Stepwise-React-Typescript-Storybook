import pytest

from apps.emissions.models import AssetSeason
from apps.wells.models import WellPlannerWellType


@pytest.fixture
def well_data():
    return {
        "sidetrack": "T001",
        "description": "Test Well Description",
        "field": "Test Field",
        "location": "Test Well Planner Location",
        "type": WellPlannerWellType.PRODUCTION,
        "fuel_type": "Marine diesel",
        "fuel_density": 850.0,
        "co2_per_fuel": 3.17,
        "nox_per_fuel": 52.0,
        "co2_tax": 0.0,
        "nox_tax": 0.0,
        "fuel_cost": 800.0,
        "boilers_co2_per_fuel": 3.17,
        "boilers_nox_per_fuel": 5,
    }


@pytest.fixture
def vessel_use_data() -> dict:
    return {
        'duration': 3.5,
        'exposure_against_current_well': 100,
        'waiting_on_weather': 0,
        'season': AssetSeason.SUMMER,
        'quota_obligation': 0,
    }


@pytest.fixture
def helicopter_use_data() -> dict:
    return {'trips': 4, 'trip_duration': 100, 'exposure_against_current_well': 100, 'quota_obligation': 10}
