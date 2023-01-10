from apps.wells.models import BaseWellPlannerStep


# v20.12.2022
# 'Calculation'!H272
def calculate_external_energy_supply_co2(
    *,
    # 'Calculation'!D261
    capacity: float,
    # 'Calculation'!E244
    co2_factor: float,
    # 'Well Planning'!J55
    # duration in days
    duration: float,
) -> float:
    return capacity * co2_factor * duration


# v20.12.2022
# 'Calculation'!I272
def calculate_external_energy_supply_nox(
    *,
    # 'Calculation'!D261
    capacity: float,
    # 'Asset & Material Inputs'!K97
    nox_factor: float,
    # 'Well Planning'!J55
    # duration in days
    duration: float,
) -> float:
    return capacity * nox_factor * duration


# v20.12.2022
# 'Calculation'!F272
def calculate_external_energy_supply_fuel_reduction(
    *,
    # 'Calculation'!D261
    capacity: float,
    # 'Calculation'!G261
    generator_efficiency: float,
    # 'Well Planning'!J55,
    duration: float,
) -> float:
    return capacity * generator_efficiency * duration


# v20.12.2022
# 'Calculation'!I196
def calculate_external_energy_supply_co2_reduction(
    *,
    # 'Calculation'!D261
    capacity: float,
    # 'Calculation'!G261
    generator_efficiency: float,
    # 'Well Planning'!J55,
    duration: float,
    # 'Well Planning'!C11
    co2_per_fuel: float,
) -> float:
    return (
        calculate_external_energy_supply_fuel_reduction(
            capacity=capacity,
            generator_efficiency=generator_efficiency,
            duration=duration,
        )
        * co2_per_fuel
    )


# v20.12.2022
# 'Calculation'!J196
def calculate_external_energy_supply_nox_reduction(
    *,
    # 'Calculation'!D261
    capacity: float,
    # 'Calculation'!G261
    generator_efficiency: float,
    # 'Well Planning'!J55,
    duration: float,
    # 'Well Planning'!D11
    fuel_density: float,
    # 'Well Planning'!F11
    nox_per_fuel: float,
) -> float:
    return (
        calculate_external_energy_supply_fuel_reduction(
            capacity=capacity,
            generator_efficiency=generator_efficiency,
            duration=duration,
        )
        * fuel_density
        * nox_per_fuel
        / 1000000
    )


# v20.12.2022
def calculate_step_external_energy_supply_co2(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    external_energy_supply = step.well_planner.asset.external_energy_supply

    return calculate_external_energy_supply_co2(
        capacity=external_energy_supply.capacity,
        co2_factor=external_energy_supply.co2,
        duration=step_duration,
    )


# v20.12.2022
def calculate_step_external_energy_supply_nox(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    external_energy_supply = step.well_planner.asset.external_energy_supply

    return calculate_external_energy_supply_nox(
        capacity=external_energy_supply.capacity,
        nox_factor=external_energy_supply.nox,
        duration=step_duration,
    )


# v20.12.2022
def calculate_step_external_energy_supply_fuel_reduction(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    external_energy_supply = step.well_planner.asset.external_energy_supply

    return calculate_external_energy_supply_fuel_reduction(
        capacity=external_energy_supply.capacity,
        generator_efficiency=external_energy_supply.generator_efficiency_factor,
        duration=step_duration,
    )


# v20.12.2022
def calculate_step_external_energy_supply_co2_reduction(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    external_energy_supply = step.well_planner.asset.external_energy_supply

    return calculate_external_energy_supply_co2_reduction(
        capacity=external_energy_supply.capacity,
        generator_efficiency=external_energy_supply.generator_efficiency_factor,
        duration=step_duration,
        co2_per_fuel=step.well_planner.co2_per_fuel,
    )


# v20.12.2022
def calculate_step_external_energy_supply_nox_reduction(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    external_energy_supply = step.well_planner.asset.external_energy_supply

    return calculate_external_energy_supply_nox_reduction(
        capacity=external_energy_supply.capacity,
        generator_efficiency=external_energy_supply.generator_efficiency_factor,
        duration=step_duration,
        fuel_density=step.well_planner.fuel_density,
        nox_per_fuel=step.well_planner.nox_per_fuel,
    )
