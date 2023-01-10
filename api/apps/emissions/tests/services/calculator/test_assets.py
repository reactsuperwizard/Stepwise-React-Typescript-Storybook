import pytest

from apps.emissions.factories import BaselineInputFactory
from apps.emissions.services.calculator.assets import (
    calculate_asset_co2,
    calculate_asset_fuel,
    calculate_asset_nox,
    calculate_step_asset_co2,
    calculate_step_asset_fuel,
    calculate_step_asset_nox,
)
from apps.wells.factories import WellPlannerPlannedStepFactory

# v20.12.22
PHASES = {
    "Phase 1": dict(
        # 'Well Planning'!H54
        baseline_fuel=130.0,
        # 'Calculation'!E239
        duration=9.555,
    ),
    "Phase 2": dict(
        # 'Well Planning'!H55
        baseline_fuel=128.75,
        # 'Well Planning'!E244
        duration=7.665,
    ),
    "Phase 3": dict(
        # 'Well Planning'!H56
        baseline_fuel=128.75,
        # 'Well Planning'!E249
        duration=3.36,
    ),
}


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        # 'Calculation'!D6
        ("Phase 1", 1242.1499999999999),
        # 'Calculation'!E6
        ("Phase 2", 986.86875),
        # 'Calculation'!F6
        ("Phase 3", 432.59999999999997),
    ),
)
def test_calculate_asset_fuel(
    phase: str,
    expected: float,
):
    assert (
        calculate_asset_fuel(
            baseline_fuel=PHASES[phase]['baseline_fuel'],
            duration=PHASES[phase]['duration'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        # 'Calculation'!D24
        ("Phase 1", 3937.6154999999994),
        # 'Calculation'!E24
        ("Phase 2", 3128.3739375),
        # 'Calculation'!F24
        ("Phase 3", 1371.3419999999999),
    ),
)
def test_calculate_asset_co2(
    phase: str,
    expected: float,
):
    assert (
        calculate_asset_co2(
            baseline_fuel=PHASES[phase]['baseline_fuel'],
            duration=PHASES[phase]['duration'],
            # 'Well Planning'!C11
            co2_per_fuel=3.17,
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        # 'Calculation'!D27
        ("Phase 1", 55.48994587499999),
        # 'Calculation'!E27 but based on 'Calculation'!E6
        ("Phase 2", 44.085894234375),
        # 'Calculation'!F27 but based on 'Calculation'!F6
        ("Phase 3", 19.3253235),
    ),
)
def test_calculate_asset_nox(
    phase: str,
    expected: float,
):
    assert (
        calculate_asset_nox(
            baseline_fuel=PHASES[phase]['baseline_fuel'],
            duration=PHASES[phase]['duration'],
            # 'Well Planning'!D11,
            fuel_density=835,
            # 'Well Planning'!F11
            nox_per_fuel=53.5,
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!D6
        ("Phase 1", 1242.1499999999999),
        # 'Calculation'!E6
        ("Phase 2", 986.86875),
        # 'Calculation'!F6
        ("Phase 3", 432.59999999999997),
    ),
)
def test_calculate_step_asset_fuel(
    phase: str,
    expected: float,
):
    step = WellPlannerPlannedStepFactory()
    BaselineInputFactory(
        baseline=step.well_planner.baseline,
        phase=step.phase,
        mode=step.mode,
        value=PHASES[phase]['baseline_fuel'],
    )
    BaselineInputFactory()

    assert (
        calculate_step_asset_fuel(
            step=step,
            step_duration=PHASES[phase]['duration'],
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        # 'Calculation'!D24
        ("Phase 1", 3937.6154999999994),
        # 'Calculation'!E24
        ("Phase 2", 3128.3739375),
        # 'Calculation'!F24
        ("Phase 3", 1371.3419999999999),
    ),
)
def test_calculate_step_asset_co2(
    phase: str,
    expected: float,
):
    step = WellPlannerPlannedStepFactory(
        # 'Well Planning'!C11
        well_planner__co2_per_fuel=3.17
    )
    BaselineInputFactory(
        baseline=step.well_planner.baseline,
        phase=step.phase,
        mode=step.mode,
        value=PHASES[phase]['baseline_fuel'],
    )
    BaselineInputFactory()

    assert (
        calculate_step_asset_co2(
            step=step,
            step_duration=PHASES[phase]['duration'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        # 'Calculation'!D27
        ("Phase 1", 55.48994587499999),
        # 'Calculation'!E27 but based on 'Calculation'!E6
        ("Phase 2", 44.085894234375),
        # 'Calculation'!F27 but based on 'Calculation'!F6
        ("Phase 3", 19.3253235),
    ),
)
def test_calculate_step_asset_nox(
    phase: str,
    expected: float,
):
    step = WellPlannerPlannedStepFactory(
        # 'Well Planning'!D11,
        well_planner__fuel_density=835,
        # 'Well Planning'!F11
        well_planner__nox_per_fuel=53.5,
    )
    BaselineInputFactory(
        baseline=step.well_planner.baseline,
        phase=step.phase,
        mode=step.mode,
        value=PHASES[phase]['baseline_fuel'],
    )
    BaselineInputFactory()

    assert (
        calculate_step_asset_nox(
            step=step,
            step_duration=PHASES[phase]['duration'],
        )
        == expected
    )
