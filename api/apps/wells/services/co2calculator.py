import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import DefaultDict, NamedTuple, TypedDict, cast

from django.db.models import QuerySet, Sum

from apps.emissions.models import (
    AssetSeason,
    BaseHelicopterUse,
    BaselineInput,
    EmissionReductionInitiative,
    EmissionReductionInitiativeInput,
    EmissionReductionInitiativeType,
    MaterialCategory,
    VesselType,
)
from apps.monitors.models import MonitorFunctionType, MonitorFunctionValue
from apps.wells.models import BaseWellPlannerStep, WellPlanner, WellPlannerCompleteStep, WellPlannerPlannedStep

logger = logging.getLogger(__name__)
CO2_FACTOR = 3.17
HELICOPTER_CO2_FACTOR = 3.16


class VesselOperation(NamedTuple):
    # number of days in operation
    duration: float
    # diesel fuel consumption in cubic meters per day
    fuel_consumption: float


class HelicopterOperation(NamedTuple):
    # number of planned flights
    trips: int
    # flight time from shore and back in minutes
    trip_duration: float
    # fuel consumption in liters per hour
    fuel_consumption: float


class WellPlannerStepCO2EmissionReductionInitiative(TypedDict):
    emission_reduction_initiative: EmissionReductionInitiative
    value: float


class WellPlannerStepCO2Result(TypedDict):
    base: float
    baseline: float
    target: float
    rig: float
    vessels: float
    helicopters: float
    cement: float
    steel: float
    external_energy_supply: float
    emission_reduction_initiatives: list[WellPlannerStepCO2EmissionReductionInitiative]


def calculate_phase_helicopters_co2(
    *,
    # days
    phase_duration: float,
    # days
    total_duration: float,
    # Kilograms of CO2 emitted per a kilogram of fuel
    co2_factor: float,
    helicopters: list[HelicopterOperation],
) -> float:
    total_fuel_consumption = sum(
        map(
            lambda helicopter: helicopter.trip_duration / 60 * helicopter.trips * helicopter.fuel_consumption,
            helicopters,
        )
    )
    # jet fuel to kg factor
    jet_fuel_to_kg_factor = 0.8
    total_co2 = total_fuel_consumption * jet_fuel_to_kg_factor * co2_factor / 1000
    co2_per_day = total_co2 / total_duration
    return co2_per_day * phase_duration


def calculate_phase_base_co2(
    *,
    # days
    phase_duration: float,
    # m3 diesel / day
    fuel_consumption: float,
    # kg CO2 / kg diesel
    co2_factor: float,
) -> float:
    return fuel_consumption * co2_factor * phase_duration


def calculate_phase_rig_co2(
    # ton
    base_co2: float,
    # total improvement from all emission reduction initiatives (ton)
    emission_reduction_initiatives_improvement: float,
) -> float:
    return base_co2 - emission_reduction_initiatives_improvement


def calculate_phase_emp_improvement_co2(
    *,
    # % improvement
    improvement: float,
    # CO2 ton
    base_co2: float,
) -> float:
    return (improvement * base_co2) / 100


def calculate_phase_vessels_co2(
    *,
    # days
    phase_duration: float,
    # days
    total_duration: float,
    # kg CO2 / kg diesel
    co2_factor: float,
    vessels: list[VesselOperation],
) -> float:
    total_fuel_consumption = sum(map(lambda vessel: vessel.duration * vessel.fuel_consumption, vessels))
    total_co2 = total_fuel_consumption * co2_factor
    co2_per_day = total_co2 / total_duration
    return co2_per_day * phase_duration


def calculate_phase_external_energy_supply_co2(
    *,
    # days
    phase_duration: float,
    # MWh/day
    capacity: float,
    # ton CO2/MWh
    co2_factor: float,
) -> float:
    co2_per_day = capacity * co2_factor * 24
    return co2_per_day * phase_duration


def calculate_phase_improved_duration(
    # days
    phase_duration: float,
    # total improvement from all productivity improvements (%)
    productivity_improvement: float,
) -> float:
    return phase_duration - (productivity_improvement * phase_duration) / 100


def calculate_phase_baseline_co2(
    *,
    # ton
    base_co2: float,
    # ton
    cement_co2: float,
    # ton
    steel_co2: float,
    # ton
    external_energy_supply_co2: float,
    # ton
    vessels_co2: float,
    # ton
    helicopters_co2: float,
) -> float:
    return base_co2 + helicopters_co2 + vessels_co2 + external_energy_supply_co2 + steel_co2 + cement_co2


def calculate_phase_target_line_co2(
    *,
    # ton
    rig_co2: float,
    # ton
    cement_co2: float,
    # ton
    steel_co2: float,
    # ton
    external_energy_supply_co2: float,
    # ton
    vessels_co2: float,
    # ton
    helicopters_co2: float,
) -> float:
    return rig_co2 + cement_co2 + steel_co2 + external_energy_supply_co2 + vessels_co2 + helicopters_co2


def calculate_phase_cement_co2(
    *,
    # m3
    cement: float,
    # ton CO2 / m3 cement
    co2_factor: float,
) -> float:
    return cement * co2_factor


def calculate_phase_steel_co2(
    *,
    # ton
    steel: float,
    # ton CO2 / ton steel
    co2_factor: float,
) -> float:
    return steel * co2_factor


def get_vessel_fuel_consumption(*, vessel_type: VesselType, season: AssetSeason) -> float:
    match season:
        case AssetSeason.WINTER:
            return vessel_type.fuel_consumption_winter
        case AssetSeason.SUMMER:
            return vessel_type.fuel_consumption_summer
        case _:
            raise ValueError(f'Unknown season: {season}')


def calculate_planned_step_improved_duration(planned_step: WellPlannerPlannedStep) -> float:
    productivity_phases = EmissionReductionInitiativeInput.objects.filter(
        phase=planned_step.phase,
        mode=planned_step.mode,
        emission_reduction_initiative__in=planned_step.emission_reduction_initiatives.filter(
            type=EmissionReductionInitiativeType.PRODUCTIVITY
        ),
    )
    productivity_improvement = sum(productivity_phase.value for productivity_phase in productivity_phases)

    improved_duration = calculate_phase_improved_duration(
        phase_duration=planned_step.total_duration,
        productivity_improvement=productivity_improvement,
    )

    return improved_duration


def multiply_well_planner_step_co2(
    well_planner_step_co2: WellPlannerStepCO2Result, mult: float
) -> WellPlannerStepCO2Result:
    if mult == 1:
        return well_planner_step_co2

    multiplied_well_planner_step_co2 = WellPlannerStepCO2Result(
        base=well_planner_step_co2['base'] * mult,
        baseline=well_planner_step_co2['baseline'] * mult,
        target=well_planner_step_co2['target'] * mult,
        rig=well_planner_step_co2['rig'] * mult,
        vessels=well_planner_step_co2['vessels'] * mult,
        helicopters=well_planner_step_co2['helicopters'] * mult,
        cement=well_planner_step_co2['cement'] * mult,
        steel=well_planner_step_co2['steel'] * mult,
        external_energy_supply=well_planner_step_co2['external_energy_supply'] * mult,
        emission_reduction_initiatives=[
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative['emission_reduction_initiative'],
                value=emission_reduction_initiative['value'] * mult,
            )
            for emission_reduction_initiative in well_planner_step_co2['emission_reduction_initiatives']
        ],
    )
    return multiplied_well_planner_step_co2


def sum_emission_reduction_initiative_improvements(
    first: list[WellPlannerStepCO2EmissionReductionInitiative],
    second: list[WellPlannerStepCO2EmissionReductionInitiative],
) -> list[WellPlannerStepCO2EmissionReductionInitiative]:
    emission_reduction_initiatives_map: DefaultDict[EmissionReductionInitiative, float] = defaultdict(float)

    for emission_reduction_initiative in [*first, *second]:
        emission_reduction_initiatives_map[
            emission_reduction_initiative['emission_reduction_initiative']
        ] += emission_reduction_initiative['value']

    return [
        WellPlannerStepCO2EmissionReductionInitiative(
            emission_reduction_initiative=key,
            value=value,
        )
        for key, value in emission_reduction_initiatives_map.items()
    ]


def substract_emission_reduction_initiative_improvements(
    first: list[WellPlannerStepCO2EmissionReductionInitiative],
    second: list[WellPlannerStepCO2EmissionReductionInitiative],
) -> list[WellPlannerStepCO2EmissionReductionInitiative]:
    emission_reduction_initiatives_map: DefaultDict[EmissionReductionInitiative, float] = defaultdict(float)

    for first_emission_reduction_initiative in first:
        emission_reduction_initiatives_map[
            first_emission_reduction_initiative['emission_reduction_initiative']
        ] = first_emission_reduction_initiative['value']

    for second_emission_reduction_initiative in second:
        emission_reduction_initiatives_map[
            second_emission_reduction_initiative['emission_reduction_initiative']
        ] -= second_emission_reduction_initiative['value']

    return [
        WellPlannerStepCO2EmissionReductionInitiative(
            emission_reduction_initiative=key,
            value=value,
        )
        for key, value in emission_reduction_initiatives_map.items()
    ]


def sum_well_planner_step_co2s(
    first: WellPlannerStepCO2Result, second: WellPlannerStepCO2Result
) -> WellPlannerStepCO2Result:

    summed_well_planner_step_co2 = WellPlannerStepCO2Result(
        base=first['base'] + second['base'],
        baseline=first['baseline'] + second['baseline'],
        target=first['target'] + second['target'],
        rig=first['rig'] + second['rig'],
        vessels=first['vessels'] + second['vessels'],
        helicopters=first['helicopters'] + second['helicopters'],
        cement=first['cement'] + second['cement'],
        steel=first['steel'] + second['steel'],
        external_energy_supply=first['external_energy_supply'] + second['external_energy_supply'],
        emission_reduction_initiatives=sum_emission_reduction_initiative_improvements(
            first['emission_reduction_initiatives'], second['emission_reduction_initiatives']
        ),
    )
    return summed_well_planner_step_co2


def subtract_well_planner_step_co2s(
    first: WellPlannerStepCO2Result, second: WellPlannerStepCO2Result
) -> WellPlannerStepCO2Result:
    helicopters = first['helicopters'] - second['helicopters']
    vessels = first['vessels'] - second['vessels']
    rounding_error = 1e-10
    subtracted_well_planner_co2 = WellPlannerStepCO2Result(
        base=first['base'] - second['base'],
        baseline=first['baseline'] - second['baseline'],
        target=first['target'] - second['target'],
        rig=first['rig'] - second['rig'],
        # fix floating point arithmetic precision error
        vessels=0 if abs(vessels) < rounding_error else vessels,
        # fix floating point arithmetic precision error
        helicopters=0 if abs(helicopters) < rounding_error else helicopters,
        cement=first['cement'] - second['cement'],
        steel=first['steel'] - second['steel'],
        external_energy_supply=first['external_energy_supply'] - second['external_energy_supply'],
        emission_reduction_initiatives=substract_emission_reduction_initiative_improvements(
            first['emission_reduction_initiatives'], second['emission_reduction_initiatives']
        ),
    )
    return subtracted_well_planner_co2


def calculate_well_planner_step_base_co2(*, well_planner_step: WellPlannerPlannedStep, duration: float) -> float:
    baseline_input = BaselineInput.objects.get(
        baseline=well_planner_step.well_planner.baseline,
        phase=well_planner_step.phase,
        mode=well_planner_step.mode,
        season=well_planner_step.season,
    )
    base_co2 = calculate_phase_base_co2(
        phase_duration=duration,
        fuel_consumption=baseline_input.value,
        co2_factor=CO2_FACTOR,
    )

    return base_co2


def calculate_well_planner_step_external_energy_supply_co2(
    *, well_planner_step: BaseWellPlannerStep, duration: float
) -> float:
    if well_planner_step.external_energy_supply_enabled:
        external_energy_supply_co2 = calculate_phase_external_energy_supply_co2(
            phase_duration=duration,
            capacity=well_planner_step.well_planner.asset.external_energy_supply.capacity,
            co2_factor=well_planner_step.well_planner.asset.external_energy_supply.co2,
        )
    else:
        external_energy_supply_co2 = 0

    return external_energy_supply_co2


def calculate_well_planner_step_cement_co2(
    well_planner_step: BaseWellPlannerStep,
) -> float:
    cement_co2 = 0.0

    for cement_material in well_planner_step.materials.select_related('material_type').filter(
        material_type__category=MaterialCategory.CEMENT
    ):
        cement_co2 += calculate_phase_cement_co2(
            cement=cement_material.quantity,
            co2_factor=cement_material.material_type.co2,
        )

    return cement_co2


def calculate_well_planner_step_steel_co2(well_planner_step: BaseWellPlannerStep) -> float:
    steel_co2 = 0.0

    for steel_material in well_planner_step.materials.select_related('material_type').filter(
        material_type__category=MaterialCategory.STEEL
    ):
        steel_co2 += calculate_phase_steel_co2(
            steel=steel_material.quantity,
            co2_factor=steel_material.material_type.co2,
        )

    return steel_co2


def calculate_well_planner_step_helicopters_co2(
    *, helicopter_uses: QuerySet[BaseHelicopterUse], duration: float, total_duration: float
) -> float:
    helicopter_operations = [
        HelicopterOperation(
            helicopter_use.trips,
            helicopter_use.trip_duration,
            helicopter_use.helicopter_type.fuel_consumption,
        )
        for helicopter_use in helicopter_uses
    ]
    helicopters_co2 = calculate_phase_helicopters_co2(
        phase_duration=duration,
        total_duration=total_duration,
        co2_factor=HELICOPTER_CO2_FACTOR,
        helicopters=helicopter_operations,
    )

    return helicopters_co2


def calculate_well_planner_step_vessels_co2(
    *, vessel_operations: list[VesselOperation], duration: float, total_season_duration: float
) -> float:
    return calculate_phase_vessels_co2(
        phase_duration=duration,
        total_duration=total_season_duration,
        co2_factor=CO2_FACTOR,
        vessels=vessel_operations,
    )


def calculate_well_planner_step_emission_reduction_initiative_improvements(
    *, well_planner_step: BaseWellPlannerStep, base_co2: float
) -> list[WellPlannerStepCO2EmissionReductionInitiative]:
    emission_reduction_initiative_improvements = []

    emission_reduction_initiative_inputs = (
        EmissionReductionInitiativeInput.objects.filter(
            emission_reduction_initiative__in=well_planner_step.emission_reduction_initiatives.exclude(
                type=EmissionReductionInitiativeType.PRODUCTIVITY
            ),
            phase=well_planner_step.phase,
            mode=well_planner_step.mode,
        )
        .select_related('emission_reduction_initiative')
        .order_by('id')
    )

    for emission_reduction_initiative_input in emission_reduction_initiative_inputs:
        value = calculate_phase_emp_improvement_co2(
            improvement=emission_reduction_initiative_input.value, base_co2=base_co2
        )
        emission_reduction_initiative_improvements.append(
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_input.emission_reduction_initiative,
                value=value,
            )
        )

    return emission_reduction_initiative_improvements


def calculate_well_planner_step_rig_co2(
    *, base_co2: float, emission_reduction_initiative_improvements: list[WellPlannerStepCO2EmissionReductionInitiative]
) -> float:
    total_emission_reduction_initiative_improvement = sum(
        emission_reduction_initiative_improvement['value']
        for emission_reduction_initiative_improvement in emission_reduction_initiative_improvements
    )
    rig_co2 = calculate_phase_rig_co2(base_co2, total_emission_reduction_initiative_improvement)

    return rig_co2


def calculate_well_planner_step_co2(
    *,
    planned_step: WellPlannerPlannedStep,
    # well planner step duration or improved duration in days
    duration: float,
    # total well planner duration in days
    total_duration: float,
    # total season duration in days
    total_season_duration: float,
) -> WellPlannerStepCO2Result:
    base_co2 = calculate_well_planner_step_base_co2(
        well_planner_step=planned_step,
        duration=duration,
    )
    external_energy_supply_co2 = calculate_well_planner_step_external_energy_supply_co2(
        well_planner_step=planned_step,
        duration=duration,
    )
    cement_co2 = calculate_well_planner_step_cement_co2(planned_step)
    steel_co2 = calculate_well_planner_step_steel_co2(planned_step)
    helicopters_co2 = calculate_well_planner_step_helicopters_co2(
        helicopter_uses=planned_step.well_planner.plannedhelicopteruse_set.all(),
        duration=duration,
        total_duration=total_duration,
    )
    vessel_operations = [
        VesselOperation(
            vessel_use.total_days,
            get_vessel_fuel_consumption(
                vessel_type=vessel_use.vessel_type, season=cast(AssetSeason, planned_step.season)
            ),
        )
        for vessel_use in planned_step.well_planner.plannedvesseluse_set.filter(season=planned_step.season)
    ]
    vessels_co2 = calculate_well_planner_step_vessels_co2(
        vessel_operations=vessel_operations, duration=duration, total_season_duration=total_season_duration
    )
    emission_reduction_initiative_improvements = calculate_well_planner_step_emission_reduction_initiative_improvements(
        well_planner_step=planned_step, base_co2=base_co2
    )
    rig_co2 = calculate_well_planner_step_rig_co2(
        base_co2=base_co2, emission_reduction_initiative_improvements=emission_reduction_initiative_improvements
    )
    baseline = calculate_phase_baseline_co2(
        base_co2=base_co2,
        cement_co2=cement_co2,
        steel_co2=steel_co2,
        external_energy_supply_co2=external_energy_supply_co2,
        vessels_co2=vessels_co2,
        helicopters_co2=helicopters_co2,
    )
    target = calculate_phase_target_line_co2(
        rig_co2=rig_co2,
        cement_co2=cement_co2,
        steel_co2=steel_co2,
        external_energy_supply_co2=external_energy_supply_co2,
        vessels_co2=vessels_co2,
        helicopters_co2=helicopters_co2,
    )

    logger.info(f"Calculated CO2 emission for WellPlannerPlannedStep(pk={planned_step.pk}).")
    return WellPlannerStepCO2Result(
        base=base_co2,
        baseline=baseline,
        target=target,
        rig=rig_co2,
        vessels=vessels_co2,
        helicopters=helicopters_co2,
        cement=cement_co2,
        steel=steel_co2,
        external_energy_supply=external_energy_supply_co2,
        emission_reduction_initiatives=emission_reduction_initiative_improvements,
    )


def get_seasons_duration(steps: list[tuple[float, AssetSeason]]) -> dict[AssetSeason, float]:
    seasons = {AssetSeason.WINTER: 0.0, AssetSeason.SUMMER: 0.0}
    for duration, season in steps:
        seasons[season] += duration

    return seasons


def calculate_total_well_planner_step_co2(well_planner: WellPlanner, improved: bool) -> WellPlannerStepCO2Result:
    def get_step_duration(step: WellPlannerPlannedStep) -> float:
        if improved:
            return step.improved_duration
        return step.total_duration

    planned_steps = well_planner.planned_steps.order_by('order')  # type: ignore
    total_step_co2 = WellPlannerStepCO2Result(
        base=0,
        baseline=0,
        target=0,
        rig=0,
        vessels=0,
        helicopters=0,
        cement=0,
        steel=0,
        external_energy_supply=0,
        emission_reduction_initiatives=[],
    )
    total_duration = sum(get_step_duration(step) for step in planned_steps)
    seasons_duration = get_seasons_duration([(get_step_duration(step), step.season) for step in planned_steps])

    for step in planned_steps:
        step_co2 = calculate_well_planner_step_co2(
            planned_step=step,
            duration=get_step_duration(step),
            total_duration=total_duration,
            total_season_duration=seasons_duration[step.season],
        )
        total_step_co2 = sum_well_planner_step_co2s(total_step_co2, step_co2)

    return total_step_co2


def calculate_well_planner_co2_improvement(well_planner: WellPlanner) -> WellPlannerStepCO2Result:
    total_regular_well_planner_step_co2 = calculate_total_well_planner_step_co2(
        well_planner=well_planner, improved=False
    )

    total_improved_well_planner_step_co2 = calculate_total_well_planner_step_co2(
        well_planner=well_planner, improved=True
    )

    well_planner_co2_improvement = subtract_well_planner_step_co2s(
        total_regular_well_planner_step_co2,
        total_improved_well_planner_step_co2,
    )
    return well_planner_co2_improvement


def calculate_measured_well_planner_step_rig_co2(
    complete_step: WellPlannerCompleteStep, start: datetime, end: datetime
) -> float:
    rig_co2 = (
        MonitorFunctionValue.objects.filter(
            monitor_function__vessel=complete_step.well_planner.asset.vessel,
            monitor_function__type=MonitorFunctionType.CO2_EMISSION,
            date__gte=start,
            date__lt=end,
            monitor_function__draft=False,
        ).aggregate(rig_co2=Sum('value'))['rig_co2']
        or 0
    )

    return rig_co2


def calculate_measured_well_planner_step_base_co2(
    *, complete_step: WellPlannerCompleteStep, measured_rig_co2: float
) -> float:
    emission_reduction_initiative_inputs = EmissionReductionInitiativeInput.objects.filter(
        emission_reduction_initiative__in=complete_step.emission_reduction_initiatives.exclude(
            type=EmissionReductionInitiativeType.PRODUCTIVITY
        ),
        phase=complete_step.phase,
        mode=complete_step.mode,
    ).order_by('id')

    total_emission_reduction_initiative_improvement = (
        sum(
            emission_reduction_initiative_input.value
            for emission_reduction_initiative_input in emission_reduction_initiative_inputs
        )
        / 100
    )

    if total_emission_reduction_initiative_improvement >= 1:
        measured_base_co2 = 0.0
    else:
        measured_base_co2 = measured_rig_co2 / (1 - total_emission_reduction_initiative_improvement)

    return measured_base_co2


def calculate_measured_well_planner_step_co2(
    *,
    complete_step: WellPlannerCompleteStep,
    start: datetime,
    end: datetime,
    total_duration: float,
    total_season_duration: float,
) -> WellPlannerStepCO2Result:
    duration = abs((start - end).total_seconds()) / int(timedelta(days=1).total_seconds())
    # fix floating point arithmetic precision error
    rounding_error = 1e-10
    assert (
        duration <= complete_step.duration or abs(duration - complete_step.duration) <= rounding_error
    ), 'Duration must be less or equal to complete step duration'

    measured_rig_co2 = calculate_measured_well_planner_step_rig_co2(complete_step, start, end)
    measured_base_co2 = calculate_measured_well_planner_step_base_co2(
        complete_step=complete_step, measured_rig_co2=measured_rig_co2
    )
    external_energy_supply_co2 = calculate_well_planner_step_external_energy_supply_co2(
        well_planner_step=complete_step, duration=duration
    )
    helicopters_co2 = calculate_well_planner_step_helicopters_co2(
        helicopter_uses=complete_step.well_planner.completehelicopteruse_set.all(),
        duration=duration,
        total_duration=total_duration,
    )
    vessel_operations = [
        VesselOperation(
            vessel_use.duration,
            get_vessel_fuel_consumption(
                vessel_type=vessel_use.vessel_type, season=cast(AssetSeason, complete_step.season)
            ),
        )
        for vessel_use in complete_step.well_planner.completevesseluse_set.filter(season=complete_step.season)
    ]
    vessels_co2 = calculate_well_planner_step_vessels_co2(
        vessel_operations=vessel_operations, duration=duration, total_season_duration=total_season_duration
    )
    emission_reduction_initiative_improvements = calculate_well_planner_step_emission_reduction_initiative_improvements(
        well_planner_step=complete_step,
        base_co2=measured_base_co2,
    )
    cement_co2 = calculate_well_planner_step_cement_co2(complete_step) * (duration / complete_step.duration)
    steel_co2 = calculate_well_planner_step_steel_co2(complete_step) * (duration / complete_step.duration)
    baseline = calculate_phase_baseline_co2(
        base_co2=measured_base_co2,
        cement_co2=cement_co2,
        steel_co2=steel_co2,
        external_energy_supply_co2=external_energy_supply_co2,
        vessels_co2=vessels_co2,
        helicopters_co2=helicopters_co2,
    )
    target = calculate_phase_target_line_co2(
        rig_co2=measured_rig_co2,
        cement_co2=cement_co2,
        steel_co2=steel_co2,
        external_energy_supply_co2=external_energy_supply_co2,
        vessels_co2=vessels_co2,
        helicopters_co2=helicopters_co2,
    )

    return WellPlannerStepCO2Result(
        base=measured_base_co2,
        baseline=baseline,
        rig=measured_rig_co2,
        target=target,
        vessels=vessels_co2,
        helicopters=helicopters_co2,
        cement=cement_co2,
        steel=steel_co2,
        external_energy_supply=external_energy_supply_co2,
        emission_reduction_initiatives=emission_reduction_initiative_improvements,
    )
