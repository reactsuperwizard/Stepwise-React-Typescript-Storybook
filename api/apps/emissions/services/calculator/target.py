from typing import TypedDict

from apps.wells.models import WellPlannerPlannedStep

from .assets import calculate_step_asset_co2, calculate_step_asset_nox
from .boilers import calculate_step_boilers_co2, calculate_step_boilers_nox
from .emission_reduction_initiatives import (
    InitiativeReductionData,
    calculate_step_emission_reduction_initiative_reductions,
    calculate_total_emission_reduction_initiative_reduction,
)
from .external_energy_supply import (
    calculate_step_external_energy_supply_co2,
    calculate_step_external_energy_supply_co2_reduction,
    calculate_step_external_energy_supply_nox,
    calculate_step_external_energy_supply_nox_reduction,
)
from .helicopters import calculate_step_helicopters_co2, calculate_step_helicopters_nox
from .materials import calculate_step_materials_co2
from .vessels import calculate_step_vessels_co2, calculate_step_vessels_nox


class TargetCO2Data(TypedDict):
    asset: float
    boilers: float
    vessels: float
    helicopters: float
    materials: float
    external_energy_supply: float
    emission_reduction_initiatives: list[InitiativeReductionData]


class TargetNOXData(TypedDict):
    asset: float
    boilers: float
    vessels: float
    helicopters: float
    external_energy_supply: float
    emission_reduction_initiatives: list[InitiativeReductionData]


# v20.12.2022
def calculate_planned_step_target_co2(
    *, planned_step: WellPlannerPlannedStep, step_duration: float, plan_duration: float, season_duration: float
) -> TargetCO2Data:
    asset_co2 = calculate_step_asset_co2(step=planned_step, step_duration=step_duration)
    boilers_co2 = calculate_step_boilers_co2(step=planned_step, step_duration=step_duration)
    vessels_co2 = calculate_step_vessels_co2(
        vessel_uses=planned_step.well_planner.plannedvesseluse_set.select_related('vessel_type'),
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
        external_energy_supply_co2_reduction = calculate_step_external_energy_supply_co2_reduction(
            step=planned_step,
            step_duration=step_duration,
        )
    else:
        external_energy_supply_co2 = 0
        external_energy_supply_co2_reduction = 0

    emission_reduction_initiative_co2_reductions = calculate_step_emission_reduction_initiative_reductions(
        baseline=asset_co2,
        step=planned_step,
    )
    total_emission_reduction_initiative_reduction = calculate_total_emission_reduction_initiative_reduction(
        initiatives=emission_reduction_initiative_co2_reductions
    )
    reduced_asset_co2 = asset_co2 - external_energy_supply_co2_reduction - total_emission_reduction_initiative_reduction

    return TargetCO2Data(
        asset=reduced_asset_co2,
        boilers=boilers_co2,
        vessels=vessels_co2,
        helicopters=helicopters_co2,
        materials=materials_co2,
        external_energy_supply=external_energy_supply_co2,
        emission_reduction_initiatives=emission_reduction_initiative_co2_reductions,
    )


def multiply_target_co2(
    target: TargetCO2Data,
    multiplier: float,
) -> TargetCO2Data:
    return TargetCO2Data(
        asset=target['asset'] * multiplier,
        boilers=target['boilers'] * multiplier,
        vessels=target['vessels'] * multiplier,
        helicopters=target['helicopters'] * multiplier,
        materials=target['materials'] * multiplier,
        external_energy_supply=target['external_energy_supply'] * multiplier,
        emission_reduction_initiatives=[
            InitiativeReductionData(
                emission_reduction_initiative_id=initiative_data['emission_reduction_initiative_id'],
                value=initiative_data['value'] * multiplier,
            )
            for initiative_data in target['emission_reduction_initiatives']
        ],
    )


# v20.12.2022
def calculate_planned_step_target_nox(
    *, planned_step: WellPlannerPlannedStep, step_duration: float, plan_duration: float, season_duration: float
) -> TargetNOXData:
    asset_nox = calculate_step_asset_nox(step=planned_step, step_duration=step_duration)
    boilers_nox = calculate_step_boilers_nox(step=planned_step, step_duration=step_duration)
    vessels_nox = calculate_step_vessels_nox(
        vessel_uses=planned_step.well_planner.plannedvesseluse_set.select_related('vessel_type'),
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
        external_energy_supply_nox_reduction = calculate_step_external_energy_supply_nox_reduction(
            step=planned_step,
            step_duration=step_duration,
        )
    else:
        external_energy_supply_nox = 0
        external_energy_supply_nox_reduction = 0

    emission_reduction_initiative_nox_reductions = calculate_step_emission_reduction_initiative_reductions(
        baseline=asset_nox,
        step=planned_step,
    )
    total_emission_reduction_initiative_reduction = calculate_total_emission_reduction_initiative_reduction(
        initiatives=emission_reduction_initiative_nox_reductions
    )
    reduced_asset_nox = asset_nox - external_energy_supply_nox_reduction - total_emission_reduction_initiative_reduction

    return TargetNOXData(
        asset=reduced_asset_nox,
        boilers=boilers_nox,
        vessels=vessels_nox,
        helicopters=helicopters_nox,
        external_energy_supply=external_energy_supply_nox,
        emission_reduction_initiatives=emission_reduction_initiative_nox_reductions,
    )


def multiply_target_nox(
    target: TargetNOXData,
    multiplier: float,
) -> TargetNOXData:
    return TargetNOXData(
        asset=target['asset'] * multiplier,
        boilers=target['boilers'] * multiplier,
        vessels=target['vessels'] * multiplier,
        helicopters=target['helicopters'] * multiplier,
        external_energy_supply=target['external_energy_supply'] * multiplier,
        emission_reduction_initiatives=[
            InitiativeReductionData(
                emission_reduction_initiative_id=initiative_data['emission_reduction_initiative_id'],
                value=initiative_data['value'] * multiplier,
            )
            for initiative_data in target['emission_reduction_initiatives']
        ],
    )
