from django.db.models import QuerySet

from apps.emissions.models import BaseHelicopterUse


# v20.12.22
# 'Calculation'!F98
def calculate_helicopter_fuel(
    *,
    # 'Well Planning'!O19
    # duration of roundtrip in minutes
    roundtrip_minutes: float,
    # 'Well Planning'!P19
    # number of roundtrips
    roundtrip_count: int,
    # 'Asset & Materials Input'!F86
    # fuel consumption in liters per hour
    fuel_consumption: float,
    # 'Well Planning'!Q19
    # exposure against current well in percentage
    exposure: float,
) -> float:
    return (roundtrip_minutes / 60) * roundtrip_count * (fuel_consumption / 1000) * (exposure / 100)


# v20.12.22
# 'Calculation'!H98
def calculate_helicopter_co2(
    *,
    # 'Well Planning'!O19
    # duration of roundtrip in minutes
    roundtrip_minutes: float,
    # 'Well Planning'!P19
    # number of roundtrips
    roundtrip_count: int,
    # 'Asset & Materials Input'!F86
    # fuel consumption in liters per hour
    fuel_consumption: float,
    # 'Well Planning'!Q19
    # exposure against current well in percentage
    exposure: float,
    # 'Asset & Materials Input'!G86
    # tons of co2 per m3 of fuel
    co2_per_fuel: float,
) -> float:
    return (
        calculate_helicopter_fuel(
            roundtrip_minutes=roundtrip_minutes,
            roundtrip_count=roundtrip_count,
            fuel_consumption=fuel_consumption,
            exposure=exposure,
        )
        * co2_per_fuel
    )


# v20.12.22
# 'Calculation'!I98
def calculate_helicopter_nox(
    *,
    # 'Well Planning'!O19
    # duration of roundtrip in minutes
    roundtrip_minutes: float,
    # 'Well Planning'!P19
    # number of roundtrips
    roundtrip_count: int,
    # 'Asset & Materials Input'!F86
    # fuel consumption in liters per hour
    fuel_consumption: float,
    # 'Well Planning'!Q19
    # exposure against current well in percentage
    exposure: float,
    # 'Asset & Materials Input'!H86
    # kg per m3 of fuel
    fuel_density: float,
    # 'Asset & Materials Input'!I86
    # kg of nox per m3 of fuel
    nox_per_fuel: float,
) -> float:
    return (
        calculate_helicopter_fuel(
            roundtrip_minutes=roundtrip_minutes,
            roundtrip_count=roundtrip_count,
            fuel_consumption=fuel_consumption,
            exposure=exposure,
        )
        * (fuel_density * nox_per_fuel)
        / 1000000
    )


# v20.12.22
# 'Calculation'!F107
def calculate_step_helicopters_fuel(
    *, helicopter_uses: QuerySet[BaseHelicopterUse], step_duration: float, plan_duration: float
) -> float:
    return sum(
        calculate_helicopter_fuel(
            roundtrip_minutes=helicopter_use.trip_duration,
            roundtrip_count=helicopter_use.trips,
            fuel_consumption=helicopter_use.helicopter_type.fuel_consumption,
            exposure=helicopter_use.exposure_against_current_well,
        )
        * step_duration
        / plan_duration
        for helicopter_use in helicopter_uses
    )


# v20.12.22
# 'Calculation'!H107
def calculate_step_helicopters_co2(
    *,
    helicopter_uses: QuerySet[BaseHelicopterUse],
    step_duration: float,
    plan_duration: float,
) -> float:
    return sum(
        calculate_helicopter_co2(
            roundtrip_minutes=helicopter_use.trip_duration,
            roundtrip_count=helicopter_use.trips,
            fuel_consumption=helicopter_use.helicopter_type.fuel_consumption,
            exposure=helicopter_use.exposure_against_current_well,
            co2_per_fuel=helicopter_use.helicopter_type.co2_per_fuel,
        )
        * step_duration
        / plan_duration
        for helicopter_use in helicopter_uses
    )


# v20.12.22
# 'Calculation'!I107
def calculate_step_helicopters_nox(
    *,
    helicopter_uses: QuerySet[BaseHelicopterUse],
    step_duration: float,
    plan_duration: float,
) -> float:
    return sum(
        calculate_helicopter_nox(
            roundtrip_minutes=helicopter_use.trip_duration,
            roundtrip_count=helicopter_use.trips,
            fuel_consumption=helicopter_use.helicopter_type.fuel_consumption,
            exposure=helicopter_use.exposure_against_current_well,
            fuel_density=helicopter_use.helicopter_type.fuel_density,
            nox_per_fuel=helicopter_use.helicopter_type.nox_per_fuel,
        )
        * step_duration
        / plan_duration
        for helicopter_use in helicopter_uses
    )
