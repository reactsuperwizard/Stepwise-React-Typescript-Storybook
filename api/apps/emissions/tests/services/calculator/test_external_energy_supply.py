import pytest

from apps.emissions.factories import ExternalEnergySupplyFactory
from apps.emissions.services.calculator.external_energy_supply import (
    calculate_external_energy_supply_co2,
    calculate_external_energy_supply_co2_reduction,
    calculate_external_energy_supply_fuel_reduction,
    calculate_external_energy_supply_nox,
    calculate_external_energy_supply_nox_reduction,
    calculate_step_external_energy_supply_co2,
    calculate_step_external_energy_supply_co2_reduction,
    calculate_step_external_energy_supply_fuel_reduction,
    calculate_step_external_energy_supply_nox,
    calculate_step_external_energy_supply_nox_reduction,
)
from apps.wells.factories import WellPlannerPlannedStepFactory
from apps.wells.models import WellPlannerPlannedStep

# v20.12.22
PHASES = {
    "Phase 2": dict(
        # 'Well Planning'!J55
        duration=6.13,
    ),
    "Phase 3": dict(
        # 'Well Planning'!J56
        duration=2.89,
    ),
}


# v20.12.22
@pytest.fixture
def step() -> WellPlannerPlannedStep:
    external_energy_supply = ExternalEnergySupplyFactory(
        # 'Calculation'!D261
        capacity=4.0,
        # 'Calculation'!G261
        generator_efficiency_factor=3.881,
        # 'Asset & Material Inputs'!I97
        co2=0.055,
        # 'Asset & Material Inputs'!K97
        nox=0.000001,
    )
    step = WellPlannerPlannedStepFactory(
        well_planner__asset=external_energy_supply.asset,
        # 'Well Planning'!D11
        well_planner__fuel_density=835.0,
        # 'Well Planning'!F11
        well_planner__nox_per_fuel=53.5,
    )
    return step


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!H272
            1.3486,
        ),
        (
            "Phase 3",
            # 'Calculation'!H279
            0.6358,
        ),
    ),
)
def test_calculate_external_energy_supply_co2(phase: str, expected: float):
    assert (
        calculate_external_energy_supply_co2(
            # 'Calculation'!D261
            capacity=4.0,
            # 'Calculation'!E261
            co2_factor=0.055,
            duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!I272
            0.00002452,
        ),
        (
            "Phase 3",
            # 'Calculation'!I279
            0.00001156,
        ),
    ),
)
def test_calculate_external_energy_supply_nox(phase: str, expected: float):
    assert (
        calculate_external_energy_supply_nox(
            # 'Calculation'!D261
            capacity=4.0,
            # 'Asset & Material Inputs'!K97
            nox_factor=0.000001,
            duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!F272
            95.16211999999999,
        ),
        (
            "Phase 3",
            # 'Calculation'!F279
            44.86436,
        ),
    ),
)
def test_calculate_external_energy_supply_fuel_reduction(phase: str, expected: float):
    assert (
        calculate_external_energy_supply_fuel_reduction(
            # 'Calculation'!D261
            capacity=4.0,
            # 'Calculation'!G261
            generator_efficiency=3.881,
            duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!I196
            301.66392039999994,
        ),
        (
            "Phase 3",
            # 'Calculation'!I220
            142.2200212,
        ),
    ),
)
def test_calculate_external_energy_supply_co2_reduction(phase: str, expected: float):
    assert (
        calculate_external_energy_supply_co2_reduction(
            # 'Calculation'!D261
            capacity=4.0,
            # 'Calculation'!G261
            generator_efficiency=3.881,
            # 'Well Planning'!C11
            co2_per_fuel=3.17,
            duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!J196
            4.2511298057,
        ),
        (
            "Phase 3",
            # 'Calculation'!J220
            2.0042031221,
        ),
    ),
)
def test_calculate_external_energy_supply_nox_reduction(phase: str, expected: float):
    assert (
        calculate_external_energy_supply_nox_reduction(
            # 'Calculation'!D261
            capacity=4.0,
            # 'Calculation'!G261
            generator_efficiency=3.881,
            # 'Well Planning'!D11
            fuel_density=835.0,
            # 'Well Planning'!F11
            nox_per_fuel=53.5,
            duration=PHASES[phase]["duration"],
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    # v20.12.22
    (
        (
            "Phase 2",
            # 'Calculation'!H272
            1.3486,
        ),
        (
            "Phase 3",
            # 'Calculation'!H279
            0.6358,
        ),
    ),
)
def test_calculate_step_external_energy_supply_co2(step: WellPlannerPlannedStep, phase: str, expected: float):
    assert (
        calculate_step_external_energy_supply_co2(
            step=step,
            step_duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!I272
            0.00002452,
        ),
        (
            "Phase 3",
            # 'Calculation'!I279
            0.00001156,
        ),
    ),
)
def test_calculate_step_external_energy_supply_nox(step: WellPlannerPlannedStep, phase: str, expected: float):
    assert (
        calculate_step_external_energy_supply_nox(
            step=step,
            step_duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!F272
            95.16211999999999,
        ),
        (
            "Phase 3",
            # 'Calculation'!F279
            44.86436,
        ),
    ),
)
def test_calculate_step_external_energy_supply_fuel_reduction(
    step: WellPlannerPlannedStep, phase: str, expected: float
):
    assert (
        calculate_step_external_energy_supply_fuel_reduction(
            step=step,
            step_duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!I196
            301.66392039999994,
        ),
        (
            "Phase 3",
            # 'Calculation'!I220
            142.2200212,
        ),
    ),
)
def test_calculate_step_external_energy_supply_co2_reduction(step: WellPlannerPlannedStep, phase: str, expected: float):
    assert (
        calculate_step_external_energy_supply_co2_reduction(
            step=step,
            step_duration=PHASES[phase]["duration"],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'phase,expected',
    (
        (
            "Phase 2",
            # 'Calculation'!J196
            4.2511298057,
        ),
        (
            "Phase 3",
            # 'Calculation'!J220
            2.0042031221,
        ),
    ),
)
def test_calculate_step_external_energy_supply_nox_reduction(step: WellPlannerPlannedStep, phase: str, expected: float):
    assert (
        calculate_step_external_energy_supply_nox_reduction(
            step=step,
            step_duration=PHASES[phase]["duration"],
        )
        == expected
    )
