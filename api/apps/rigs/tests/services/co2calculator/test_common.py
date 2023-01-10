import datetime

import pytest

from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.rigs.factories import CustomDrillshipFactory, CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import RigStatus
from apps.rigs.services.co2calculator.common import (
    HelicopterResult,
    PSVResult,
    RigStatusResult,
    calculate_custom_helicopter,
    calculate_custom_psv,
    calculate_custom_rig_status,
    calculate_helicopter,
    calculate_psv,
    calculate_rig_age_score,
    calculate_rig_status,
    calculate_well_difficulty,
)
from apps.wells.factories import CustomWellFactory
from apps.wells.models import SimpleMediumDemanding, WellType


@pytest.mark.django_db
@pytest.mark.freeze_time('2022-05-11')
@pytest.mark.parametrize(
    'delivery_date, score',
    (
        (datetime.date(day=1, month=10, year=2025), 10),
        (datetime.date(day=1, month=10, year=2022), 10),
        (datetime.date(day=1, month=10, year=2021), 9.666666666666666),
        (datetime.date(day=1, month=10, year=2007), 5.0),
        (datetime.date(day=1, month=10, year=1993), 0.3333333333333339),
        (datetime.date(day=1, month=10, year=1992), 0),
        (datetime.date(day=1, month=10, year=1990), 0),
    ),
)
def test_calculate_rig_age_score(delivery_date, score):
    assert calculate_rig_age_score(delivery_date) == score


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                rig_status=RigStatus.DRILLING,
                months_in_operation_last_year=6,
                months_in_operation_last_3_years=18,
                delivery_date=datetime.date(day=1, month=4, year=2013),
            ),
            RigStatusResult(
                points=23.0, status=4.0000, last_year_continuity=6.0000, last_3_year_continuity=6.0000, rig_age=7.0
            ),
        ),
        (
            'Concept CJ62',
            dict(
                rig_status=RigStatus.DRILLING,
                months_in_operation_last_year=6,
                months_in_operation_last_3_years=18,
                delivery_date=datetime.date(day=3, month=1, year=1993),
            ),
            RigStatusResult(
                points=16.333333333333336,
                status=4.0000,
                last_year_continuity=6.0000,
                last_3_year_continuity=6.0000,
                rig_age=0.3333333333333339,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                rig_status=RigStatus.DRILLING,
                months_in_operation_last_year=6,
                months_in_operation_last_3_years=18,
                delivery_date=datetime.date(day=21, month=7, year=2009),
            ),
            RigStatusResult(
                points=21.666666666666664,
                status=4.0000,
                last_year_continuity=6.0000,
                last_3_year_continuity=6.0000,
                rig_age=5.666666666666666,
            ),
        ),
        (
            'Concept N Class',
            dict(
                rig_status=RigStatus.DRILLING,
                months_in_operation_last_year=6,
                months_in_operation_last_3_years=18,
                delivery_date=datetime.date(day=16, month=2, year=2011),
            ),
            RigStatusResult(
                points=22.333333333333336,
                status=4.0000,
                last_year_continuity=6.0000,
                last_3_year_continuity=6.0000,
                rig_age=6.333333333333334,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                rig_status=RigStatus.DRILLING,
                months_in_operation_last_year=6,
                months_in_operation_last_3_years=18,
                delivery_date=datetime.date(day=26, month=6, year=2000),
            ),
            RigStatusResult(
                points=18.666666666666668,
                status=4.0000,
                last_year_continuity=6.0000,
                last_3_year_continuity=6.0000,
                rig_age=2.666666666666667,
            ),
        ),
    ),
)
def test_calculate_rig_status(name, input, output):
    result = calculate_rig_status(**input)

    assert result == output


@pytest.mark.django_db
@pytest.mark.parametrize('RigFactory', (CustomJackupRigFactory, CustomSemiRigFactory, CustomDrillshipFactory))
def test_calculate_custom_rig_status(RigFactory):
    rig = RigFactory(
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=1, month=4, year=2013),
    )
    assert calculate_custom_rig_status(rig) == RigStatusResult(
        points=23.0, status=4.0000, last_year_continuity=6.0000, last_3_year_continuity=6.0000, rig_age=7.0
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'well_type, well_difficulty, trips_per_well, total_fuel_consumption',
    (
        (
            WellType.PRODUCTION,
            SimpleMediumDemanding.SIMPLE,
            12.621428571428572,
            122.53303571428573,
        ),
        (
            WellType.PRODUCTION,
            SimpleMediumDemanding.MEDIUM,
            13.285714285714286,
            128.98214285714286,
        ),
        (
            WellType.PRODUCTION,
            SimpleMediumDemanding.DEMANDING,
            15.942857142857143,
            154.77857142857144,
        ),
        (
            WellType.EXPLORATION,
            SimpleMediumDemanding.SIMPLE,
            10.62857142857143,
            103.18571428571431,
        ),
        (
            WellType.EXPLORATION,
            SimpleMediumDemanding.MEDIUM,
            13.285714285714286,
            128.98214285714286,
        ),
        (
            WellType.EXPLORATION,
            SimpleMediumDemanding.DEMANDING,
            15.278571428571428,
            148.3294642857143,
        ),
        (WellType.PNA, SimpleMediumDemanding.SIMPLE, 10.62857142857143, 103.18571428571431),
        (WellType.PNA, SimpleMediumDemanding.MEDIUM, 13.285714285714286, 128.98214285714286),
        (WellType.PNA, SimpleMediumDemanding.DEMANDING, 15.278571428571428, 148.3294642857143),
    ),
)
def test_calculate_psv(well_type, well_difficulty, trips_per_well, total_fuel_consumption):
    assert calculate_psv(
        days=62,
        psv_visits_per_7_days=1.5000,
        distance_from_shore_nm=100,
        psv_speed_kn=12,
        fuel_transit_consumption_td=12.0000,
        fuel_dp_consumption_td=5.5000,
        loading_time_d=0.2500,
        well_type=well_type,
        well_difficulty=well_difficulty,
    ) == PSVResult(
        time_per_trip_d=0.9444444444444445,
        trips_per_well=trips_per_well,
        fuel_transit_consumption=8.333333333333334,
        fuel_consumption_at_rig=1.3750,
        fuel_consumption_per_trip=9.708333333333334,
        total_fuel_consumption=total_fuel_consumption,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'type, top_hole, transport_section, reservoir_section, completion, pna, difficulty',
    (
        (
            WellType.PRODUCTION,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
        ),
        (
            WellType.PRODUCTION,
            SimpleMediumDemanding.MEDIUM,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.MEDIUM,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.DEMANDING,
        ),
        (
            WellType.EXPLORATION,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.MEDIUM,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.MEDIUM,
        ),
        (
            WellType.PNA,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.SIMPLE,
            SimpleMediumDemanding.DEMANDING,
            SimpleMediumDemanding.DEMANDING,
        ),
    ),
)
def test_calculate_well_difficulty(type, top_hole, transport_section, reservoir_section, completion, pna, difficulty):
    well = CustomWellFactory(
        type=type,
        top_hole=top_hole,
        transport_section=transport_section,
        reservoir_section=reservoir_section,
        completion=completion,
        pna=pna,
    )

    assert calculate_well_difficulty(well) == difficulty


@pytest.mark.django_db
def test_calculate_custom_psv():
    project = ProjectFactory(
        psv_calls_per_week=1.5000,
        psv_speed=12,
        psv_avg_fuel_transit_consumption=12.0000,
        psv_avg_fuel_dp_consumption=5.5000,
        psv_loading_time=0.2500,
    )
    plan = PlanFactory(project=project)
    well = CustomWellFactory(
        project=project,
        type=WellType.PRODUCTION,
        top_hole=SimpleMediumDemanding.SIMPLE,
        transport_section=SimpleMediumDemanding.SIMPLE,
        reservoir_section=SimpleMediumDemanding.SIMPLE,
        completion=SimpleMediumDemanding.SIMPLE,
        pna=SimpleMediumDemanding.SIMPLE,
    )
    plan_well = PlanWellRelationFactory(
        well=well,
        plan=plan,
        distance_to_psv_base=100,
    )

    assert calculate_custom_psv(days=62, plan_well=plan_well,) == PSVResult(
        time_per_trip_d=0.9444444444444445,
        trips_per_well=12.621428571428572,
        fuel_transit_consumption=8.333333333333334,
        fuel_consumption_at_rig=1.3750,
        fuel_consumption_per_trip=9.708333333333334,
        total_fuel_consumption=122.53303571428573,
    )


@pytest.mark.django_db
def test_calculate_helicopter():
    assert calculate_helicopter(
        helicopter_trips_per_7_days=1.5000,
        distance_from_base=110.0000,
        cruise_speed_kn=120.0000,
        fuel_consumption_td=12.0000,
        days=62,
        quarters_capacity=145,
    ) == HelicopterResult(
        fuel_consumption_roundtrip_t=0.9166666666666665,
        helicopter_trips=13.285714285714286,
        total_fuel_consumption_t=12.178571428571427,
        factor=1.0550,
    )


@pytest.mark.django_db
@pytest.mark.parametrize('rig_factory', (CustomJackupRigFactory, CustomSemiRigFactory))
def test_calculate_custom_helicopter(rig_factory):
    project = ProjectFactory(
        helicopter_no_flights_per_week=1.5000,
        helicopter_avg_fuel_consumption=12.0000,
        helicopter_cruise_speed=120.000,
    )
    rig = rig_factory(
        project=project,
        quarters_capacity=145,
    )
    plan_well = PlanWellRelationFactory(
        plan__project=project,
        distance_to_helicopter_base=110.0000,
    )
    assert calculate_custom_helicopter(plan_well=plan_well, rig=rig, days=62,) == HelicopterResult(
        fuel_consumption_roundtrip_t=0.9166666666666665,
        helicopter_trips=13.285714285714286,
        total_fuel_consumption_t=12.178571428571427,
        factor=1.0550,
    )
