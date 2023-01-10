from typing import TypedDict

from apps.wells.models import WellPlannerPlannedStep

from .assets import calculate_step_asset_co2, calculate_step_asset_nox
from .boilers import calculate_step_boilers_co2, calculate_step_boilers_nox
from .external_energy_supply import calculate_step_external_energy_supply_co2, calculate_step_external_energy_supply_nox
from .helicopters import calculate_step_helicopters_co2, calculate_step_helicopters_nox
from .materials import calculate_step_materials_co2
from .vessels import calculate_step_vessels_co2, calculate_step_vessels_nox


class BaselineCO2Data(TypedDict):
    asset: float
    boilers: float
    vessels: float
    helicopters: float
    materials: float
    external_energy_supply: float


class BaselineNOXData(TypedDict):
    asset: float
    boilers: float
    vessels: float
    helicopters: float
    external_energy_supply: float


# v20.12.2022
def calculate_planned_step_baseline_co2(
    *, planned_step: WellPlannerPlannedStep, step_duration: float, plan_duration: float, season_duration: float
) -> BaselineCO2Data:
    asset_co2 = calculate_step_asset_co2(step=planned_step, step_duration=step_duration)
    boilers_co2 = calculate_step_boilers_co2(step=planned_step, step_duration=step_duration)
    vessels_co2 = calculate_step_vessels_co2(
        vessel_uses=planned_step.well_planner.plannedvesseluse_set.filter(season=planned_step.season).select_related(
            'vessel_type'
        ),
        step_duration=step_duration,
        season_duration=season_duration,
    )
    helicopters_co2 = calculate_step_helicopters_co2(
        helicopter_uses=planned_step.well_planner.plannedhelicopteruse_set.select_related('helicopter_type'),
        step_duration=step_duration,
        plan_duration=plan_duration,
    )
    materials_co2 = calculate_step_materials_co2(materials=planned_step.materials.select_related('material_type'))

    if planned_step.external_energy_supply_enabled:
        external_energy_supply_co2 = calculate_step_external_energy_supply_co2(
            step=planned_step,
            step_duration=step_duration,
        )
    else:
        external_energy_supply_co2 = 0

    return BaselineCO2Data(
        asset=asset_co2,
        boilers=boilers_co2,
        vessels=vessels_co2,
        helicopters=helicopters_co2,
        materials=materials_co2,
        external_energy_supply=external_energy_supply_co2,
    )


def multiply_baseline_co2(
    baseline: BaselineCO2Data,
    multiplier: float,
) -> BaselineCO2Data:
    return BaselineCO2Data(
        asset=baseline['asset'] * multiplier,
        boilers=baseline['boilers'] * multiplier,
        vessels=baseline['vessels'] * multiplier,
        helicopters=baseline['helicopters'] * multiplier,
        materials=baseline['materials'] * multiplier,
        external_energy_supply=baseline['external_energy_supply'] * multiplier,
    )


def calculate_planned_step_baseline_nox(
    *, planned_step: WellPlannerPlannedStep, step_duration: float, plan_duration: float, season_duration: float
) -> BaselineNOXData:
    asset_nox = calculate_step_asset_nox(step=planned_step, step_duration=step_duration)
    boilers_nox = calculate_step_boilers_nox(step=planned_step, step_duration=step_duration)
    vessels_nox = calculate_step_vessels_nox(
        vessel_uses=planned_step.well_planner.plannedvesseluse_set.filter(season=planned_step.season).select_related(
            'vessel_type'
        ),
        step_duration=step_duration,
        season_duration=season_duration,
    )
    helicopters_nox = calculate_step_helicopters_nox(
        helicopter_uses=planned_step.well_planner.plannedhelicopteruse_set.select_related('helicopter_type'),
        step_duration=step_duration,
        plan_duration=plan_duration,
    )

    if planned_step.external_energy_supply_enabled:
        external_energy_supply_nox = calculate_step_external_energy_supply_nox(
            step=planned_step,
            step_duration=step_duration,
        )
    else:
        external_energy_supply_nox = 0

    return BaselineNOXData(
        asset=asset_nox,
        boilers=boilers_nox,
        vessels=vessels_nox,
        helicopters=helicopters_nox,
        external_energy_supply=external_energy_supply_nox,
    )


def multiply_baseline_nox(
    baseline: BaselineNOXData,
    multiplier: float,
) -> BaselineNOXData:
    return BaselineNOXData(
        asset=baseline['asset'] * multiplier,
        boilers=baseline['boilers'] * multiplier,
        vessels=baseline['vessels'] * multiplier,
        helicopters=baseline['helicopters'] * multiplier,
        external_energy_supply=baseline['external_energy_supply'] * multiplier,
    )
