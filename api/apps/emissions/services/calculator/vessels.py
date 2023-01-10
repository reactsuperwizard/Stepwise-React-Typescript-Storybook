from django.db.models import QuerySet

from apps.emissions.models import BaseVesselUse


# v20.12.22
# 'Calculation'!H59
def calculate_vessel_fuel(
    *,
    # 'Well Planning'!F19
    # vessel use duration
    duration: float,
    # 'Well Planning'!H19
    # waiting on weather in percentage
    waiting_on_weather: float,
    # 'Calculation'!G59
    # fuel consumption in liters per day in m3
    fuel_consumption: float,
    # 'Well Planning'!I19
    # exposure against current well in percentage
    exposure: float,
) -> float:
    return duration * (1 + waiting_on_weather / 100) * (exposure / 100) * fuel_consumption


# v20.12.22
# 'Calculation'!J59
def calculate_vessel_co2(
    *,
    # 'Well Planning'!F19
    # vessel use duration
    duration: float,
    # 'Well Planning'!H19
    # waiting on weather in percentage
    waiting_on_weather: float,
    # 'Calculation'!G59
    # fuel consumption in liters per day in m3
    fuel_consumption: float,
    # 'Well Planning'!I19
    # exposure against current well in percentage
    exposure: float,
    # 'Asset & Material Inputs'!G71
    # tons of co2 per m3 of fuel
    co2_per_fuel: float,
) -> float:
    return (
        calculate_vessel_fuel(
            duration=duration,
            waiting_on_weather=waiting_on_weather,
            fuel_consumption=fuel_consumption,
            exposure=exposure,
        )
        * co2_per_fuel
    )


# v20.12.22
# 'Calculation'!K59
def calculate_vessel_nox(
    *,
    # 'Well Planning'!F19
    # vessel use duration
    duration: float,
    # 'Well Planning'!H19
    # waiting on weather in percentage
    waiting_on_weather: float,
    # 'Calculation'!G59
    # fuel consumption in liters per day in m3
    fuel_consumption: float,
    # 'Well Planning'!I19
    # exposure against current well in percentage
    exposure: float,
    # 'Asset & Material Inputs'!H71
    # kg per m3 of fuel
    fuel_density: float,
    # 'Asset & Material Inputs'!I71
    # kg of nox per ton of fuel
    nox_per_fuel: float,
) -> float:
    return (
        calculate_vessel_fuel(
            duration=duration,
            waiting_on_weather=waiting_on_weather,
            fuel_consumption=fuel_consumption,
            exposure=exposure,
        )
        * fuel_density
        * nox_per_fuel
        / 1000000
    )


# v20.12.22
def calculate_step_vessels_fuel(
    *,
    vessel_uses: QuerySet[BaseVesselUse],
    step_duration: float,
    season_duration: float,
) -> float:
    return sum(
        calculate_vessel_fuel(
            duration=vessel_use.duration,
            waiting_on_weather=vessel_use.waiting_on_weather,
            fuel_consumption=vessel_use.fuel_consumption,
            exposure=vessel_use.exposure_against_current_well,
        )
        * step_duration
        / season_duration
        for vessel_use in vessel_uses
    )


# v20.12.22
def calculate_step_vessels_co2(
    *,
    vessel_uses: QuerySet[BaseVesselUse],
    step_duration: float,
    season_duration: float,
) -> float:
    return sum(
        calculate_vessel_co2(
            duration=vessel_use.duration,
            waiting_on_weather=vessel_use.waiting_on_weather,
            fuel_consumption=vessel_use.fuel_consumption,
            exposure=vessel_use.exposure_against_current_well,
            co2_per_fuel=vessel_use.vessel_type.co2_per_fuel,
        )
        * step_duration
        / season_duration
        for vessel_use in vessel_uses
    )


# v20.12.22
def calculate_step_vessels_nox(
    *,
    vessel_uses: QuerySet[BaseVesselUse],
    step_duration: float,
    season_duration: float,
) -> float:
    return sum(
        calculate_vessel_nox(
            duration=vessel_use.duration,
            waiting_on_weather=vessel_use.waiting_on_weather,
            fuel_consumption=vessel_use.fuel_consumption,
            exposure=vessel_use.exposure_against_current_well,
            fuel_density=vessel_use.vessel_type.fuel_density,
            nox_per_fuel=vessel_use.vessel_type.nox_per_fuel,
        )
        * step_duration
        / season_duration
        for vessel_use in vessel_uses
    )
