import logging

from apps.emissions.models import AssetSeason
from apps.emissions.models.assets import Baseline
from apps.wells.models import WellPlannerPlannedStep

logger = logging.getLogger(__name__)


# v20.12.22
# 'Calculation'!H290
def calculate_boilers_fuel(
    *,
    # 'Calculation!G290
    # fuel consumption in m3 per day
    fuel_consumption: float,
    # 'Calculation'!E239
    # planned duration in days
    duration: float,
) -> float:
    return fuel_consumption * duration


# v20.12.22
# 'Calculation'!J290
def calculate_boilers_co2(
    *,
    # 'Calculation!G290
    # fuel consumption in m3 per day
    fuel_consumption: float,
    # 'Calculation'!E239
    # planned duration in days
    duration: float,
    # 'Well Planning'!N11
    # ton of co2 per m3 of fuel
    co2_per_fuel: float,
) -> float:
    return (
        calculate_boilers_fuel(
            fuel_consumption=fuel_consumption,
            duration=duration,
        )
        * co2_per_fuel
    )


# v20.12.22
# 'Calculation'!K290
def calculate_boilers_nox(
    # 'Calculation!G290
    # fuel consumption in m3 per day
    fuel_consumption: float,
    # 'Calculation'!E239
    # planned duration in days
    duration: float,
    # 'Well Planning'!D11
    # fuel density in ton per m3
    fuel_density: float,
    # 'Well Planning'!O11
    # kg of nox per ton of fuel
    nox_per_fuel: float,
) -> float:
    return (
        calculate_boilers_fuel(
            fuel_consumption=fuel_consumption,
            duration=duration,
        )
        * (fuel_density * nox_per_fuel)
        / 1000000
    )


def get_boiler_fuel_consumption(baseline: Baseline, season: AssetSeason) -> float:
    match season:
        case AssetSeason.SUMMER:
            return baseline.boilers_fuel_consumption_summer
        case AssetSeason.WINTER:
            return baseline.boilers_fuel_consumption_winter

    raise ValueError(f"Unknown season: {season}")


# v20.12.22
def calculate_step_boilers_fuel(
    *,
    step: WellPlannerPlannedStep,
    duration: float,
) -> float:
    fuel_consumption = get_boiler_fuel_consumption(baseline=step.well_planner.baseline, season=step.season)  # type: ignore

    return calculate_boilers_fuel(
        fuel_consumption=fuel_consumption,
        duration=duration,
    )


# v20.12.22
def calculate_step_boilers_co2(
    *,
    step: WellPlannerPlannedStep,
    step_duration: float,
) -> float:
    fuel_consumption = get_boiler_fuel_consumption(baseline=step.well_planner.baseline, season=step.season)  # type: ignore

    return calculate_boilers_co2(
        fuel_consumption=fuel_consumption, duration=step_duration, co2_per_fuel=step.well_planner.boilers_co2_per_fuel
    )


# v20.12.22
def calculate_step_boilers_nox(
    *,
    step: WellPlannerPlannedStep,
    step_duration: float,
) -> float:
    fuel_consumption = get_boiler_fuel_consumption(baseline=step.well_planner.baseline, season=step.season)  # type: ignore

    return calculate_boilers_nox(
        fuel_consumption=fuel_consumption,
        duration=step_duration,
        fuel_density=step.well_planner.fuel_density,
        nox_per_fuel=step.well_planner.boilers_nox_per_fuel,
    )
