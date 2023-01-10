from apps.wells.models import BaseWellPlannerStep


# v20.12.22
# 'Calculation'!D6
def calculate_asset_fuel(
    *,
    # 'Well Planning'!H54
    # baseline fuel in m3
    baseline_fuel: float,
    # Calculation'!E239
    # planned duration
    duration: float,
) -> float:
    return baseline_fuel * duration


# v20.12.22
# 'Calculation'!D24
def calculate_asset_co2(
    *,
    # 'Well Planning'!H54
    # baseline fuel in m3
    baseline_fuel: float,
    # Calculation'!E239
    # planned duration
    duration: float,
    # 'Well Planning'!C11
    # ton of co2 per m3 of fuel
    co2_per_fuel: float,
) -> float:
    return (
        calculate_asset_fuel(
            baseline_fuel=baseline_fuel,
            duration=duration,
        )
        * co2_per_fuel
    )


# v20.12.22
# 'Calculation'!D24
def calculate_asset_nox(
    *,
    # 'Well Planning'!H54
    # baseline fuel in m3
    baseline_fuel: float,
    # Calculation'!E239
    # planned duration
    duration: float,
    # 'Well Planning'!D11
    # fuel density in kg per m3
    fuel_density: float,
    # 'Well Planning'!F11
    # kg of nox per ton of fuel
    nox_per_fuel: float,
) -> float:
    return (
        calculate_asset_fuel(
            baseline_fuel=baseline_fuel,
            duration=duration,
        )
        * (fuel_density * nox_per_fuel)
        / 1000000
    )


# v20.12.22
# 'Calculation'!D6
def calculate_step_asset_fuel(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    baseline_input = step.well_planner.baseline.baselineinput_set.get(
        season=step.season,
        phase=step.phase,
        mode=step.mode,
    )

    return calculate_asset_fuel(
        baseline_fuel=baseline_input.value,
        duration=step_duration,
    )


# v20.12.22
# 'Calculation'!D24
def calculate_step_asset_co2(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    baseline_input = step.well_planner.baseline.baselineinput_set.get(
        season=step.season,
        phase=step.phase,
        mode=step.mode,
    )

    return calculate_asset_co2(
        baseline_fuel=baseline_input.value,
        duration=step_duration,
        co2_per_fuel=step.well_planner.co2_per_fuel,
    )


# v20.12.22'
# 'Calculation'!D27
def calculate_step_asset_nox(
    *,
    step: BaseWellPlannerStep,
    step_duration: float,
) -> float:
    baseline_input = step.well_planner.baseline.baselineinput_set.get(
        season=step.season,
        phase=step.phase,
        mode=step.mode,
    )

    return calculate_asset_nox(
        baseline_fuel=baseline_input.value,
        duration=step_duration,
        fuel_density=step.well_planner.fuel_density,
        nox_per_fuel=step.well_planner.nox_per_fuel,
    )
