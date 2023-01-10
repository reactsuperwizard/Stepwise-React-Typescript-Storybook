import logging

import pytest

from apps.emissions.models.assets import AssetSeason
from apps.emissions.services.calculator.boilers import (
    calculate_boilers_co2,
    calculate_boilers_fuel,
    calculate_boilers_nox,
    calculate_step_boilers_co2,
    calculate_step_boilers_fuel,
    calculate_step_boilers_nox,
)
from apps.wells.factories import WellPlannerPlannedStepFactory

logger = logging.getLogger(__name__)


# v20.12.22
PHASES = {
    "Phase 1": dict(
        # 'Calculation'!G307
        fuel_consumption=1.0,
        # 'Well Planning'!J54
        duration=9.56,
        # 'Well Planning'!F54
        season=AssetSeason.SUMMER,
    ),
    "Phase 2": dict(
        # 'Calculation'!G315
        fuel_consumption=1.5,
        # 'Well Planning'!J55
        duration=6.13,
        # 'Well Planning'!F55
        season=AssetSeason.WINTER,
    ),
    "Phase 3": dict(
        # 'Calculation'!G323
        fuel_consumption=1.5,
        # 'Well Planning'!J56
        duration=2.89,
        # 'Well Planning'!F56
        season=AssetSeason.WINTER,
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!H290
        ("Phase 1", 9.56),
        # 'Calculation'!H298
        ("Phase 2", 9.195),
        # 'Calculation'!H306
        ("Phase 3", 4.335),
    ),
)
def test_calculate_boilers_fuel(phase: str, expected: float):
    assert (
        calculate_boilers_fuel(
            fuel_consumption=PHASES[phase]['fuel_consumption'],
            duration=PHASES[phase]['duration'],
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!J290
        ("Phase 1", 30.3052),
        # 'Calculation'!J298
        ("Phase 2", 29.14815),
        # 'Calculation'!J306
        ("Phase 3", 13.74195),
    ),
)
def test_calculate_boilers_co2(phase: str, expected: float):
    assert (
        calculate_boilers_co2(
            fuel_consumption=PHASES[phase]['fuel_consumption'],
            duration=PHASES[phase]['duration'],
            # 'Well Planning'!N11
            co2_per_fuel=3.17,
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!K290
        ("Phase 1", 0.039913),
        # 'Calculation'!K298
        ("Phase 2", 0.038389125),
        # 'Calculation'!K306
        ("Phase 3", 0.018098625),
    ),
)
def test_calculate_boilers_nox(phase: str, expected: float):
    assert (
        calculate_boilers_nox(
            fuel_consumption=PHASES[phase]['fuel_consumption'],
            duration=PHASES[phase]['duration'],
            # 'Well Planning'!D11
            fuel_density=835.0,
            # 'Well Planning'!O11
            nox_per_fuel=5,
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!H290
        ("Phase 1", 9.56),
        # 'Calculation'!H298
        ("Phase 2", 9.195),
        # 'Calculation'!H306
        ("Phase 3", 4.335),
    ),
)
def test_calculate_step_boilers_fuel(phase: str, expected: float):
    step = WellPlannerPlannedStepFactory(
        season=PHASES[phase]["season"],
        # 'Asset & Material Inputs'!D50
        well_planner__baseline__boilers_fuel_consumption_summer=1.0,
        # 'Asset & Material Inputs'!E50
        well_planner__baseline__boilers_fuel_consumption_winter=1.5,
    )

    assert calculate_step_boilers_fuel(step=step, duration=PHASES[phase]["duration"]) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!J290
        ("Phase 1", 30.3052),
        # 'Calculation'!J298
        ("Phase 2", 29.14815),
        # 'Calculation'!J306
        ("Phase 3", 13.74195),
    ),
)
def test_calculate_step_boilers_co2(phase: str, expected: float):
    step = WellPlannerPlannedStepFactory(
        season=PHASES[phase]["season"],
        # 'Well Planning'!N11
        well_planner__boilers_co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!D50
        well_planner__baseline__boilers_fuel_consumption_summer=1.0,
        # 'Asset & Material Inputs'!E50
        well_planner__baseline__boilers_fuel_consumption_winter=1.5,
    )

    assert calculate_step_boilers_co2(step=step, step_duration=PHASES[phase]["duration"]) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!K290
        ("Phase 1", 0.039913),
        # 'Calculation'!K298
        ("Phase 2", 0.038389125),
        # 'Calculation'!K306
        ("Phase 3", 0.018098625),
    ),
)
def test_calculate_step_boilers_nox(phase: str, expected: float):
    step = WellPlannerPlannedStepFactory(
        season=PHASES[phase]["season"],
        # 'Asset & Material Inputs'!D50
        well_planner__baseline__boilers_fuel_consumption_summer=1.0,
        # 'Asset & Material Inputs'!E50
        well_planner__baseline__boilers_fuel_consumption_winter=1.5,
        # 'Well Planning'!D11
        well_planner__fuel_density=835.0,
        # 'Well Planning'!O11
        well_planner__boilers_nox_per_fuel=5.0,
    )

    assert calculate_step_boilers_nox(step=step, step_duration=PHASES[phase]["duration"]) == expected
