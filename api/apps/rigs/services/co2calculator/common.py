import datetime
import logging
from typing import TypedDict, cast

from django.utils import timezone

from apps.projects.models import Plan, PlanWellRelation
from apps.rigs.models import CustomJackupRig, CustomJackupSubareaScore, CustomSemiRig, CustomSemiSubareaScore, RigStatus
from apps.wells.models import CustomWell, SimpleMediumDemanding, WellType

logger = logging.getLogger(__name__)

HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL = 3.16


def calculate_rig_age_score(
    # 'JU NCS database'!G
    # 'Semi database NCS'!G
    delivery_date: datetime.date,
) -> float:
    # Linear 10 (@this year) to 0 (@30 years ago)
    # =IFS(
    #     GESTEP(10 - (YEAR(TODAY()) - YEAR('Semi database NCS'!G)) / 30 * 10; 10); 10;
    #     GESTEP(10 - (YEAR(TODAY()) - YEAR('Semi database NCS'!G)) / 30 * 10; 0); 10 - (YEAR(TODAY()) - YEAR('Semi database NCS'!G)) / 30 * 10;
    #     TRUE; 0
    # )
    rig_age_score = 10 - (timezone.now().year - delivery_date.year) / 30 * 10
    if rig_age_score > 10:
        return 10.0
    elif rig_age_score < 0:
        return 0.0
    return rig_age_score


# =IFS(
#     OR('JU NCS database'!F="Drilling");4;
#     OR('JU NCS database'!F="Under construction");0;
#     OR('JU NCS database'!F="Warm stacked");1;
#     OR('JU NCS database'!F="Cold stacked");0;
#     OR('JU NCS database'!F="Mobilizing");2;
#     TRUE;0
# )
# =IFS(
#     OR('Semi NCS database'!F="Drilling");4;
#     OR('Semi NCS database'!F="Under construction");0;
#     OR('Semi NCS database'!F="Warm stacked");1;
#     OR('Semi NCS database'!F="Cold stacked");0;
#     OR('Semi NCS database'!F="Mobilizing");2;
#     TRUE;0
# )
RIG_STATUS_SCORE = {
    RigStatus.DRILLING: 4,
    RigStatus.UNDER_CONSTRUCTION: 0,
    RigStatus.WARM_STACKED: 1,
    RigStatus.COLD_STACKED: 0,
    RigStatus.MOBILIZING: 2,
}


class RigStatusResult(TypedDict):
    points: float
    status: float
    last_year_continuity: float
    last_3_year_continuity: float
    rig_age: float


def calculate_rig_status(
    *,
    # 'JU NCS database'!F
    # 'Semi database NCS'!F
    rig_status: RigStatus,
    # 'JU NCS database'!J
    # 'Semi database NCS'!J
    months_in_operation_last_year: int,
    # 'JU NCS database'!K
    # 'Semi database NCS'!K
    months_in_operation_last_3_years: int,
    # 'JU NCS database'!G
    # 'Semi database NCS'!G
    delivery_date: datetime.date,
) -> RigStatusResult:
    logger.info('Calculating rig status')
    status_score = RIG_STATUS_SCORE[rig_status]
    # ='JU NCS database'!J
    # ='Semi database NCS'!J
    last_year_continuity_score = months_in_operation_last_year
    # ='JU NCS database'!K/3
    # ='Semi database NCS'!K/3
    last_3_year_continuity_score = months_in_operation_last_3_years / 3.0
    rig_age_score = calculate_rig_age_score(delivery_date)
    points = sum([status_score, last_year_continuity_score, last_3_year_continuity_score, rig_age_score])
    logger.info('Calculated rig status')
    return RigStatusResult(
        points=points,
        status=status_score,
        last_year_continuity=last_year_continuity_score,
        last_3_year_continuity=last_3_year_continuity_score,
        rig_age=rig_age_score,
    )


def calculate_custom_rig_status(rig: CustomJackupRig | CustomSemiRig) -> RigStatusResult:
    logger.info('Calculating rig status for %s(pk=%s)', rig.__class__.__name__, rig.pk)
    return calculate_rig_status(
        rig_status=rig.rig_status,
        months_in_operation_last_year=rig.months_in_operation_last_year,
        months_in_operation_last_3_years=rig.months_in_operation_last_3_years,
        delivery_date=rig.delivery_date,
    )


class PSVResult(TypedDict):
    time_per_trip_d: float
    trips_per_well: float
    fuel_transit_consumption: float
    fuel_consumption_at_rig: float
    fuel_consumption_per_trip: float
    total_fuel_consumption: float


PSV_WELL_FACTOR = {
    WellType.PRODUCTION: {
        SimpleMediumDemanding.SIMPLE: 0.95,
        SimpleMediumDemanding.MEDIUM: 1,
        SimpleMediumDemanding.DEMANDING: 1.2,
    },
    WellType.EXPLORATION: {
        SimpleMediumDemanding.SIMPLE: 0.8,
        SimpleMediumDemanding.MEDIUM: 1,
        SimpleMediumDemanding.DEMANDING: 1.15,
    },
    WellType.PNA: {
        SimpleMediumDemanding.SIMPLE: 0.8,
        SimpleMediumDemanding.MEDIUM: 1,
        SimpleMediumDemanding.DEMANDING: 1.15,
    },
}


def calculate_psv(
    *,
    # B3
    days: float,
    # B4
    psv_visits_per_7_days: float,
    # B5
    distance_from_shore_nm: float,
    # B6
    psv_speed_kn: float,
    # B8
    fuel_transit_consumption_td: float,
    # B9
    fuel_dp_consumption_td: float,
    # B10
    loading_time_d: float,
    well_type: WellType,
    well_difficulty: SimpleMediumDemanding,
) -> PSVResult:
    logger.info('Calculating PSV')
    # B7=2*B5/B6/24+B10
    time_per_trip_d = 2 * distance_from_shore_nm / psv_speed_kn / 24 + loading_time_d
    # B16=B3*B4/7
    trips_per_general_well = days * psv_visits_per_7_days / 7
    # =$B$16*C
    trips_per_well = trips_per_general_well * PSV_WELL_FACTOR[well_type][well_difficulty]
    # B17=(2*B5*(B8/B6))/24
    fuel_transit_consumption = (2 * distance_from_shore_nm * (fuel_transit_consumption_td / psv_speed_kn)) / 24
    # B18=B9*B10
    fuel_consumption_at_rig = fuel_dp_consumption_td * loading_time_d
    # B19=B17+B18
    fuel_consumption_per_trip = fuel_transit_consumption + fuel_consumption_at_rig
    # B20=B16*B19
    total_fuel_consumption = trips_per_well * fuel_consumption_per_trip
    logger.info('Calculated PSV')
    return PSVResult(
        time_per_trip_d=time_per_trip_d,
        trips_per_well=trips_per_well,
        fuel_transit_consumption=fuel_transit_consumption,
        fuel_consumption_at_rig=fuel_consumption_at_rig,
        fuel_consumption_per_trip=fuel_consumption_per_trip,
        total_fuel_consumption=total_fuel_consumption,
    )


WELL_DIFFICULTY_TO_SCORE = {
    SimpleMediumDemanding.SIMPLE: 1,
    SimpleMediumDemanding.MEDIUM: 2,
    SimpleMediumDemanding.DEMANDING: 3,
}

SCORE_TO_WELL_DIFFICULTY = {
    1: SimpleMediumDemanding.SIMPLE,
    2: SimpleMediumDemanding.MEDIUM,
    3: SimpleMediumDemanding.DEMANDING,
}


def calculate_well_difficulty(well: CustomWell) -> SimpleMediumDemanding:
    if well.type == WellType.PNA:
        return cast(SimpleMediumDemanding, well.pna)
    if well.type in [WellType.PRODUCTION, WellType.EXPLORATION]:
        average_score = round(
            sum(
                [
                    WELL_DIFFICULTY_TO_SCORE[well.top_hole],
                    WELL_DIFFICULTY_TO_SCORE[well.transport_section],
                    WELL_DIFFICULTY_TO_SCORE[well.reservoir_section],
                    WELL_DIFFICULTY_TO_SCORE[well.completion],
                    WELL_DIFFICULTY_TO_SCORE[well.pna],
                ]
            )
            / 5
        )
        return SCORE_TO_WELL_DIFFICULTY[average_score]

    raise NotImplementedError(f'Unknown well type: {well.type}')


def calculate_custom_psv(
    *,
    plan_well: PlanWellRelation,
    days: float,
) -> PSVResult:
    logger.info('Calculating PSV for PlanWellRelation(pk=%s) and %s days', plan_well.pk, days)
    plan = plan_well.plan
    project = plan.project
    well = plan_well.well
    return calculate_psv(
        days=days,
        psv_visits_per_7_days=project.psv_calls_per_week,
        distance_from_shore_nm=plan_well.distance_to_psv_base,
        psv_speed_kn=project.psv_speed,
        fuel_transit_consumption_td=project.psv_avg_fuel_transit_consumption,
        fuel_dp_consumption_td=project.psv_avg_fuel_dp_consumption,
        loading_time_d=project.psv_loading_time,
        well_type=well.type,
        well_difficulty=calculate_well_difficulty(well),
    )


class HelicopterResult(TypedDict):
    fuel_consumption_roundtrip_t: float
    helicopter_trips: float
    total_fuel_consumption_t: float
    factor: float


def calculate_helicopter(
    *,
    # B2
    helicopter_trips_per_7_days: float,
    # B3
    distance_from_base: float,
    # B4
    cruise_speed_kn: float,
    # B5
    fuel_consumption_td: float,
    # B10
    days: float,
    # 'JU NCS database'!N, 'Semi database NCS'!P
    quarters_capacity: float,
) -> HelicopterResult:
    logger.info('Calculating helicopter')
    # B6,B13=(B3*2/B4/24)*B5
    fuel_consumption_roundtrip_t = (distance_from_base * 2 / cruise_speed_kn / 24) * fuel_consumption_td
    # B12=B10*(B3/7)
    helicopter_trips = days * helicopter_trips_per_7_days / 7
    # B14=B6*B12
    total_fuel_consumption_t = fuel_consumption_roundtrip_t * helicopter_trips
    # C=1+(200-quarters_capacity)/1000
    factor = 1 + (200 - quarters_capacity) / 1000
    logger.info('Calculated helicopter')
    return HelicopterResult(
        fuel_consumption_roundtrip_t=fuel_consumption_roundtrip_t,
        helicopter_trips=helicopter_trips,
        total_fuel_consumption_t=total_fuel_consumption_t,
        factor=factor,
    )


def calculate_custom_helicopter(
    *,
    plan_well: PlanWellRelation,
    rig: CustomJackupRig | CustomSemiRig,
    days: float,
) -> HelicopterResult:
    logger.info(
        'Calculating helicopter for PlanWellRelation(pk=%s), %s(pk=%s) and %s days',
        plan_well.pk,
        rig.__class__.__name__,
        rig.pk,
        days,
    )
    project = plan_well.plan.project
    return calculate_helicopter(
        helicopter_trips_per_7_days=project.helicopter_no_flights_per_week,
        distance_from_base=plan_well.distance_to_helicopter_base,
        cruise_speed_kn=project.helicopter_cruise_speed,
        fuel_consumption_td=project.helicopter_avg_fuel_consumption,
        days=days,
        quarters_capacity=rig.quarters_capacity,
    )


def calculate_well_reference_operational_days(*, plan: Plan, plan_well: PlanWellRelation) -> float:
    from apps.rigs.services.co2calculator.jackup import calculate_jackup_well_reference_operational_days
    from apps.rigs.services.co2calculator.semi import (
        calculate_custom_semi_metocean_factor,
        calculate_semi_well_reference_operational_days,
    )

    if plan.reference_operation_jackup:
        reference_rig = plan.reference_operation_jackup
        rig_efficiency = CustomJackupSubareaScore.objects.get_or_calculate(reference_rig).efficiency
        return calculate_jackup_well_reference_operational_days(
            efficiency=rig_efficiency, operational_days=plan_well.operational_time
        )
    elif plan.reference_operation_semi:
        reference_rig = plan.reference_operation_semi
        rig_efficiency = CustomSemiSubareaScore.objects.get_or_calculate(reference_rig).efficiency
        weather_factor = calculate_custom_semi_metocean_factor(rig=reference_rig, well=plan_well.well)
        return calculate_semi_well_reference_operational_days(
            efficiency=rig_efficiency, operational_days=plan_well.operational_time, weather_factor=weather_factor
        )

    raise NotImplementedError('Unsupported reference rig')
