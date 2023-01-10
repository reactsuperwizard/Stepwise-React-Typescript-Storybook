import datetime
from unittest.mock import MagicMock

import pytest
import vcr
from axes.utils import reset
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from apps.privacy.models import PrivacyPolicy
from apps.rigs.factories import CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import Airgap, CustomJackupRig, CustomSemiRig, HighMediumLow, RigStatus, TopsideDesign
from apps.studies.models import StudyMetric


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(autouse=True)
def remove_active_policy():
    PrivacyPolicy.objects.filter(is_active=True).delete()


@pytest.fixture(autouse=True)
def reset_lockouts():
    reset()


@pytest.fixture(autouse=True)
def remove_study_metrics():
    StudyMetric.objects.all().delete()


@pytest.fixture
def request_recorder() -> vcr.VCR:
    return vcr.VCR(
        serializer="json",
        cassette_library_dir="apps",
        record_mode="once",
        match_on=["url", "method"],
        filter_headers=[("Authorization", "REDACTED")],
    )


@pytest.fixture
def valid_kims_vessel_id() -> str:
    """A test vessel id in the KIMS API used by success cassette"""
    return 'OSV1'


@pytest.fixture
def invalid_kims_vessel_id() -> str:
    """A test vessel id in the KIMS API used by error cassette"""
    return 'OSV2'


@pytest.fixture
def valid_kims_tag_id() -> str:
    """A test tag id in the KIMS API used by success cassette"""
    return 'Power_DGx_Load_kW'


@pytest.fixture
def invalid_kims_tag_id() -> str:
    """A test tag id in the KIMS API used by error cassette"""
    return 'Power_Capacity'


@pytest.fixture()
def clear_haystack():
    from django.core.management import call_command

    call_command('clear_index', interactive=False)


@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache

    cache.clear()


@pytest.fixture()
def concept_cj70() -> CustomJackupRig:
    return CustomJackupRigFactory(
        hull_breadth=320.0000,
        hull_depth=40.0000,
        hull_length=310.0000,
        quarters_capacity=145.0000,
        generator_quantity=4.0000,
        engine_quantity=4.0000,
        mud_total_power=7750.0000,
        drawworks_power=5359.09090909091,
        hybrid=False,
        closed_bus=False,
        derrick_height=210.0000,
        generator_power=2900.0000,
        engine_power=4200.0000,
        hvac_heat_recovery=False,
        freshwater_cooling_systems=False,
        seawater_cooling_systems=False,
        operator_awareness_dashboard=False,
        hpu_optimization=False,
        optimized_heat_tracing_system=False,
        floodlighting_optimization=False,
        vfds_on_aux_machinery=False,
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=1, month=4, year=2013),
        enhanced_legs=False,
        leg_spacing=229.0000,
        design_score=HighMediumLow.MEDIUM,
        topside_design=TopsideDesign.NOV,
        mudpump_quantity=3.0000,
        liquid_mud=9960.0000,
        offline_stand_building=True,
        auto_pipe_handling=True,
        dual_activity=False,
        drilltronic=False,
        dynamic_drilling_guide=False,
        process_automation_platform=False,
        automatic_tripping=False,
        variable_load=12509.6363636364,
        cantilever_reach=104.545454545455,
        cantilever_lateral=35.8181818181818,
        total_cranes=3.0000,
        crane_capacity=85.0000,
        rig_water_depth=490.0000,
        cantilever_capacity=3114717.09090909,
        total_bop_rams=4.0000,
        bop_diameter_wp_max=18.7500,
        subsea_drilling=True,
        tugs_no_used=3,
        jack_up_time=1.4,
        jack_down_time=1.4,
        day_rate=300000.0000,
        spread_cost=300000.0000,
    )


@pytest.fixture()
def concept_cs60() -> CustomSemiRig:
    return CustomSemiRigFactory(
        equipment_load=HighMediumLow.HIGH,
        quarters_capacity=160,
        hull_design_eco_score=4,
        dp=True,
        total_anchors=8,
        displacement=74045.2857142857,
        hull_breadth=267,
        hull_depth=168,
        hull_length=384,
        derrick_height=212,
        dual_derrick=False,
        drawworks_power=7460,
        mud_total_power=8800,
        engine_power=7350,
        engine_quantity=7,
        generator_power=5500,
        generator_quantity=7,
        closed_bus=False,
        hybrid=False,
        hvac_heat_recovery=False,
        freshwater_cooling_systems=False,
        seawater_cooling_systems=False,
        operator_awareness_dashboard=False,
        hpu_optimization=False,
        optimized_heat_tracing_system=False,
        floodlighting_optimization=False,
        vfds_on_aux_machinery=False,
        topside_design=TopsideDesign.NOV,
        drillfloor_efficiency=HighMediumLow.MEDIUM,
        tripsaver=True,
        offline_stand_building=True,
        auto_pipe_handling=True,
        dual_activity=True,
        drilltronic=False,
        dynamic_drilling_guide=False,
        process_automation_platform=False,
        automatic_tripping=False,
        variable_load=7366,
        total_cranes=2,
        crane_capacity=108,
        hull_concept_score=9.0000,
        airgap=Airgap.M,
        active_heave_drawwork=True,
        cmc_with_active_heave=True,
        ram_system=False,
        engine_total=51450.0000,
        generator_total=38500.0000,
        rig_water_depth=10000.0000,
        derrick_capacity=2272750,
        total_bop_rams=6,
        bop_diameter_wp_max=18.7500,
        bop_wp_max=15000,
        number_of_bop_stacks=1,
        mudpump_quantity=4,
        liquid_mud=16619.0000,
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=4, month=7, year=2019),
        tugs_no_used=0,
        move_speed=6.0000,
        day_rate=300000,
        spread_cost=350000,
    )


@pytest.fixture()
def concept_h3():
    return CustomSemiRigFactory(
        equipment_load=HighMediumLow.LOW,
        quarters_capacity=100,
        hull_design_eco_score=10,
        dp=False,
        thruster_assist=True,
        total_anchors=8,
        displacement=26053.5,
        hull_breadth=221,
        hull_depth=120.0000,
        hull_length=355,
        derrick_height=184,
        dual_derrick=False,
        drawworks_power=3000,
        mud_total_power=4800,
        engine_power=3648,
        engine_quantity=4,
        generator_power=2650,
        generator_quantity=4,
        closed_bus=False,
        hybrid=False,
        hvac_heat_recovery=False,
        freshwater_cooling_systems=False,
        seawater_cooling_systems=False,
        operator_awareness_dashboard=False,
        hpu_optimization=False,
        optimized_heat_tracing_system=False,
        floodlighting_optimization=False,
        vfds_on_aux_machinery=False,
        topside_design=TopsideDesign.NOV,
        drillfloor_efficiency=HighMediumLow.MEDIUM,
        tripsaver=False,
        offline_stand_building=False,
        auto_pipe_handling=False,
        dual_activity=False,
        drilltronic=False,
        dynamic_drilling_guide=False,
        process_automation_platform=False,
        automatic_tripping=False,
        variable_load=3448,
        total_cranes=2,
        crane_capacity=45,
        hull_concept_score=8.0000,
        airgap=Airgap.XL,
        active_heave_drawwork=False,
        cmc_with_active_heave=False,
        ram_system=True,
        engine_total=14592.0000,
        generator_total=10600.0000,
        rig_water_depth=1500.0000,
        derrick_capacity=1102425,
        total_bop_rams=4,
        bop_diameter_wp_max=18.7500,
        bop_wp_max=12500,
        number_of_bop_stacks=1,
        mudpump_quantity=3,
        liquid_mud=4054.5000,
        tugs_no_used=2,
        day_rate=300000,
        spread_cost=300000,
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=14, month=9, year=1987),
    )


@pytest.fixture
def mock_sync_all_plan_co2_calculations_task(mocker: MockerFixture) -> MagicMock:
    mock_sync_all_plan_co2_calculations_task = mocker.patch("apps.rigs.tasks.sync_all_plan_co2_calculations_task.delay")
    return mock_sync_all_plan_co2_calculations_task


@pytest.fixture
def mock_sync_custom_jackup_plan_co2_task(mocker: MockerFixture) -> MagicMock:
    mock_sync_custom_jackup_plan_co2_task = mocker.patch("apps.rigs.tasks.sync_custom_jackup_plan_co2_task.delay")
    return mock_sync_custom_jackup_plan_co2_task


@pytest.fixture
def mock_sync_custom_semi_plan_co2_task(mocker: MockerFixture) -> MagicMock:
    mock_sync_custom_semi_plan_co2_task = mocker.patch("apps.rigs.tasks.sync_custom_semi_plan_co2_task.delay")
    return mock_sync_custom_semi_plan_co2_task
