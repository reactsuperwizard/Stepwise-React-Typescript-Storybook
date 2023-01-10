import pytest

from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.rigs.factories import CustomJackupRigFactory
from apps.rigs.models import CustomJackupRig, HighMediumLow, TopsideDesign
from apps.rigs.services.co2calculator.jackup import (
    JackupCapacitiesResult,
    JackupCO2PerWellResult,
    JackupCO2Result,
    JackupDeckEfficiencyResult,
    JackupMoveAndInstallationResult,
    JackupMoveResult,
    JackupTopsideEfficiencyResult,
    calculate_custom_jackup_capacities,
    calculate_custom_jackup_capacities_score,
    calculate_custom_jackup_co2,
    calculate_custom_jackup_co2_per_well,
    calculate_custom_jackup_co2_score,
    calculate_custom_jackup_deck_efficiency,
    calculate_custom_jackup_deck_efficiency_score,
    calculate_custom_jackup_move,
    calculate_custom_jackup_move_and_installation,
    calculate_custom_jackup_move_and_installation_score,
    calculate_custom_jackup_rig_status_score,
    calculate_custom_jackup_topside_efficiency,
    calculate_custom_jackup_topside_efficiency_score,
    calculate_custom_jackup_well_operational_days,
    calculate_jackup_capacities,
    calculate_jackup_co2,
    calculate_jackup_co2_per_well,
    calculate_jackup_deck_efficiency,
    calculate_jackup_move,
    calculate_jackup_move_and_installation,
    calculate_jackup_topside_efficiency,
    calculate_jackup_well_operational_days,
    calculate_jackup_well_reference_operational_days,
    calculate_reference_jackup_capacities,
    calculate_reference_jackup_co2,
    calculate_reference_jackup_deck_efficiency,
    calculate_reference_jackup_move_and_installation,
    calculate_reference_jackup_rig_status,
    calculate_reference_jackup_topside_efficiency,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                hull_breadth_ft=320.0000,
                hull_depth_ft=40.0000,
                hull_length_ft=310.0000,
                quarters_capacity=145.0000,
                generator_qty_1=4.0000,
                engine_qty_1=4.0000,
                mud_total_hp=7750.0000,
                drawworks_hp=5359.09090909091,
                hybrid=False,
                closed_bus=False,
                generator_kw_1=2900.0000,
                engine_hp_1=4200.0000,
                hvac_heat_recovery=False,
                freshwater_cooling_systems=False,
                seawater_cooling_systems=False,
                operator_awareness_dashboard=False,
                hpu_optimization=False,
                optimized_heat_tracing_system=False,
                floodlighting_optimization=False,
                vfds_on_aux_machinery=False,
            ),
            JackupCO2Result(
                points=59.29375757575758,
                vessel_size=3.9680,
                accommodation=9.666666666666666,
                generator_sets_score=6.0000,
                generator_set_hp_average=2.9000,
                engine_sets_score=6.0,
                engine_set_hp_average=4.2000,
                mudpumps_hp_total=7.7500,
                drawworks_hp=5.35909090909091,
                hybrid=3.0000,
                closed_bus=3.0000,
                hvac_heat_recovery=1.5000,
                freshwater_cooling_systems=1.0000,
                seawater_cooling_systems=2.0000,
                operator_awareness_dashboard=0.7500,
                hpu_optimization=0.5000,
                optimized_heat_tracing_system=1.0000,
                floodlighting_optimization=0.2000,
                vfds_on_aux_machinery=0.5000,
            ),
        ),
        (
            'Concept CJ62',
            dict(
                hull_breadth_ft=296.0000,
                hull_depth_ft=35.0000,
                hull_length_ft=256.0000,
                quarters_capacity=118.0000,
                generator_qty_1=5.0000,
                engine_qty_1=5.0000,
                mud_total_hp=6600.0000,
                drawworks_hp=3000.0000,
                hybrid=False,
                closed_bus=False,
                generator_kw_1=1530.0000,
                engine_hp_1=1512.0000,
                hvac_heat_recovery=False,
                freshwater_cooling_systems=False,
                seawater_cooling_systems=False,
                operator_awareness_dashboard=False,
                hpu_optimization=False,
                optimized_heat_tracing_system=False,
                floodlighting_optimization=False,
                vfds_on_aux_machinery=False,
            ),
            JackupCO2Result(
                points=46.61082666666667,
                vessel_size=2.65216,
                accommodation=7.866666666666666,
                generator_sets_score=5.0000,
                generator_set_hp_average=1.5300,
                engine_sets_score=5.0,
                engine_set_hp_average=1.5120,
                mudpumps_hp_total=6.6000,
                drawworks_hp=3.0000,
                hybrid=3.0000,
                closed_bus=3.0000,
                hvac_heat_recovery=1.5000,
                freshwater_cooling_systems=1.0000,
                seawater_cooling_systems=2.0000,
                operator_awareness_dashboard=0.7500,
                hpu_optimization=0.5000,
                optimized_heat_tracing_system=1.0000,
                floodlighting_optimization=0.2000,
                vfds_on_aux_machinery=0.5000,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                hull_breadth_ft=223.0000,
                hull_depth_ft=31.0000,
                hull_length_ft=229.0000,
                quarters_capacity=120.0000,
                generator_qty_1=4.0000,
                engine_qty_1=4.0000,
                mud_total_hp=6600.0000,
                drawworks_hp=4500.0000,
                hybrid=False,
                closed_bus=False,
                generator_kw_1=2675.0000,
                engine_hp_1=3554.0000,
                hvac_heat_recovery=False,
                freshwater_cooling_systems=False,
                seawater_cooling_systems=False,
                operator_awareness_dashboard=False,
                hpu_optimization=False,
                optimized_heat_tracing_system=False,
                floodlighting_optimization=False,
                vfds_on_aux_machinery=False,
            ),
            JackupCO2Result(
                points=52.362077,
                vessel_size=1.583077,
                accommodation=8.0000,
                generator_sets_score=6.0000,
                generator_set_hp_average=2.6750,
                engine_sets_score=6.0,
                engine_set_hp_average=3.5540,
                mudpumps_hp_total=6.6000,
                drawworks_hp=4.5000,
                hybrid=3.0000,
                closed_bus=3.0000,
                hvac_heat_recovery=1.5000,
                freshwater_cooling_systems=1.0000,
                seawater_cooling_systems=2.0000,
                operator_awareness_dashboard=0.7500,
                hpu_optimization=0.5000,
                optimized_heat_tracing_system=1.0000,
                floodlighting_optimization=0.2000,
                vfds_on_aux_machinery=0.5000,
            ),
        ),
        (
            'Concept N Class',
            dict(
                hull_breadth_ft=289.0000,
                hull_depth_ft=35.0000,
                hull_length_ft=264.0000,
                quarters_capacity=120.0000,
                generator_qty_1=4.0000,
                engine_qty_1=4.0000,
                mud_total_hp=6600.0000,
                drawworks_hp=4600.0000,
                hybrid=False,
                closed_bus=False,
                generator_kw_1=2400.0000,
                engine_hp_1=3220.0000,
                hvac_heat_recovery=False,
                freshwater_cooling_systems=False,
                seawater_cooling_systems=False,
                operator_awareness_dashboard=False,
                hpu_optimization=False,
                optimized_heat_tracing_system=False,
                floodlighting_optimization=False,
                vfds_on_aux_machinery=False,
            ),
            JackupCO2Result(
                points=52.940360000000005,
                vessel_size=2.67036,
                accommodation=8.0000,
                generator_sets_score=6.0000,
                generator_set_hp_average=2.4000,
                engine_sets_score=6.0,
                engine_set_hp_average=3.2200,
                mudpumps_hp_total=6.6000,
                drawworks_hp=4.6000,
                hybrid=3.0000,
                closed_bus=3.0000,
                hvac_heat_recovery=1.5000,
                freshwater_cooling_systems=1.0000,
                seawater_cooling_systems=2.0000,
                operator_awareness_dashboard=0.7500,
                hpu_optimization=0.5000,
                optimized_heat_tracing_system=1.0000,
                floodlighting_optimization=0.2000,
                vfds_on_aux_machinery=0.5000,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                hull_breadth_ft=300.0000,
                hull_depth_ft=36.0000,
                hull_length_ft=306.0000,
                quarters_capacity=120.0000,
                generator_qty_1=6.0000,
                engine_qty_1=5.0000,
                mud_total_hp=8800.0000,
                drawworks_hp=4000.0000,
                hybrid=False,
                closed_bus=False,
                generator_kw_1=2400.0000,
                engine_hp_1=3395.0000,
                hvac_heat_recovery=False,
                freshwater_cooling_systems=False,
                seawater_cooling_systems=False,
                operator_awareness_dashboard=False,
                hpu_optimization=False,
                optimized_heat_tracing_system=False,
                floodlighting_optimization=False,
                vfds_on_aux_machinery=False,
            ),
            JackupCO2Result(
                points=52.3498,
                vessel_size=3.3048,
                accommodation=8.0000,
                generator_sets_score=4.0000,
                generator_set_hp_average=2.4000,
                engine_sets_score=5.0,
                engine_set_hp_average=3.3950,
                mudpumps_hp_total=8.8000,
                drawworks_hp=4.0000,
                hybrid=3.0000,
                closed_bus=3.0000,
                hvac_heat_recovery=1.5000,
                freshwater_cooling_systems=1.0000,
                seawater_cooling_systems=2.0000,
                operator_awareness_dashboard=0.7500,
                hpu_optimization=0.5000,
                optimized_heat_tracing_system=1.0000,
                floodlighting_optimization=0.2000,
                vfds_on_aux_machinery=0.5000,
            ),
        ),
    ),
)
def test_calculate_jackup_co2(name, input, output):
    result = calculate_jackup_co2(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_reference_jackup_co2():
    assert calculate_reference_jackup_co2()['points'] == 59.29375757575758


@pytest.mark.django_db
def test_calculate_custom_jackup_co2(concept_cj70):
    assert calculate_custom_jackup_co2(concept_cj70) == JackupCO2Result(
        points=59.29375757575758,
        vessel_size=3.9680,
        accommodation=9.666666666666666,
        generator_sets_score=6.0000,
        generator_set_hp_average=2.9000,
        engine_sets_score=6.0,
        engine_set_hp_average=4.2000,
        mudpumps_hp_total=7.7500,
        drawworks_hp=5.35909090909091,
        hybrid=3.0000,
        closed_bus=3.0000,
        hvac_heat_recovery=1.5000,
        freshwater_cooling_systems=1.0000,
        seawater_cooling_systems=2.0000,
        operator_awareness_dashboard=0.7500,
        hpu_optimization=0.5000,
        optimized_heat_tracing_system=1.0000,
        floodlighting_optimization=0.2000,
        vfds_on_aux_machinery=0.5000,
    )


@pytest.mark.django_db
def test_calculate_custom_jackup_co2_score(concept_cj70):
    assert calculate_custom_jackup_co2_score(concept_cj70) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                enhanced_legs=False,
                leg_spacing_1_ft=229.0000,
            ),
            JackupMoveAndInstallationResult(points=6.1450, rig_management=5, enhanced_legs=0, leg_spacing=1.1450),
        ),
        (
            'Concept CJ62',
            dict(
                enhanced_legs=False,
                leg_spacing_1_ft=203.0000,
            ),
            JackupMoveAndInstallationResult(points=6.0150, rig_management=5, enhanced_legs=0, leg_spacing=1.0150),
        ),
        (
            'Concept CJ50',
            dict(
                enhanced_legs=False,
                leg_spacing_1_ft=229.0000,
            ),
            JackupMoveAndInstallationResult(points=6.1450, rig_management=5, enhanced_legs=0, leg_spacing=1.1450),
        ),
        (
            'Concept N Class',
            dict(
                enhanced_legs=False,
                leg_spacing_1_ft=206.0000,
            ),
            JackupMoveAndInstallationResult(points=6.0300, rig_management=5, enhanced_legs=0, leg_spacing=1.0300),
        ),
        (
            'Concept Super Gorilla',
            dict(
                enhanced_legs=False,
                leg_spacing_1_ft=218.0000,
            ),
            JackupMoveAndInstallationResult(points=6.0900, rig_management=5, enhanced_legs=0, leg_spacing=1.0900),
        ),
    ),
)
def test_calculate_jackup_move_and_installation(name, input, output):
    result = calculate_jackup_move_and_installation(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_reference_jackup_move_and_installation():
    assert calculate_reference_jackup_move_and_installation()['points'] == 6.145


@pytest.mark.django_db
def test_calculate_custom_jackup_move_and_installation(concept_cj70):
    assert calculate_custom_jackup_move_and_installation(concept_cj70) == JackupMoveAndInstallationResult(
        points=6.1450, rig_management=5, enhanced_legs=0, leg_spacing=1.1450
    )


@pytest.mark.django_db
def test_calculate_custom_jackup_move_and_installation_score(concept_cj70):
    assert calculate_custom_jackup_move_and_installation_score(concept_cj70) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                design_score=HighMediumLow.MEDIUM,
                topside_design=TopsideDesign.NOV,
                derrick_height_ft=210.0000,
                mudpump_qty=3.0000,
                liquid_mud_bbl=9960.0000,
                mud_total_hp=7750.0000,
                offline_stand_building=True,
                auto_pipe_handling=True,
                dual_activity=False,
                drilltronic=False,
                dynamic_drilling_guide=False,
                process_automation_platform=False,
                automatic_tripping=False,
            ),
            JackupTopsideEfficiencyResult(
                points=22.4020486176822,
                design_score=1.0000,
                topside_design=1.0300,
                derrick_height_ft=2.4705882352941178,
                mudpump_qty=3.0600,
                liquid_mud_bbl=10.070778564206268,
                mud_total_hp=0.8806818181818182,
                offline_stand_building=1.9800,
                auto_pipe_handling=1.9100,
                dual_activity=0.0000,
                drilltronic=0.0000,
                dynamic_drilling_guide=0.0000,
                process_automation_platform=0.0000,
                automatic_tripping=0.0000,
            ),
        ),
        (
            'Concept CJ62',
            dict(
                design_score=HighMediumLow.MEDIUM,
                topside_design=TopsideDesign.NOV,
                derrick_height_ft=160.0000,
                mudpump_qty=3.0000,
                liquid_mud_bbl=5190.0000,
                mud_total_hp=6600.0000,
                offline_stand_building=True,
                auto_pipe_handling=False,
                dual_activity=False,
                drilltronic=False,
                dynamic_drilling_guide=False,
                process_automation_platform=False,
                automatic_tripping=False,
            ),
            JackupTopsideEfficiencyResult(
                points=14.950077915898412,
                design_score=1.0000,
                topside_design=1.0300,
                derrick_height_ft=1.8823529411764706,
                mudpump_qty=3.0600,
                liquid_mud_bbl=5.247724974721941,
                mud_total_hp=0.7500,
                offline_stand_building=1.9800,
                auto_pipe_handling=0.0000,
                dual_activity=0.0000,
                drilltronic=0.0000,
                dynamic_drilling_guide=0.0000,
                process_automation_platform=0.0000,
                automatic_tripping=0.0000,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                design_score=HighMediumLow.MEDIUM,
                topside_design=TopsideDesign.NOV,
                derrick_height_ft=210.0000,
                mudpump_qty=3.0000,
                liquid_mud_bbl=6290.0000,
                mud_total_hp=6600.0000,
                offline_stand_building=True,
                auto_pipe_handling=False,
                dual_activity=False,
                drilltronic=False,
                dynamic_drilling_guide=False,
                process_automation_platform=False,
                automatic_tripping=False,
            ),
            JackupTopsideEfficiencyResult(
                points=16.650547790400285,
                design_score=1.0000,
                topside_design=1.0300,
                derrick_height_ft=2.4705882352941178,
                mudpump_qty=3.0600,
                liquid_mud_bbl=6.359959555106168,
                mud_total_hp=0.7500,
                offline_stand_building=1.9800,
                auto_pipe_handling=0.0000,
                dual_activity=0.0000,
                drilltronic=0.0000,
                dynamic_drilling_guide=0.0000,
                process_automation_platform=0.0000,
                automatic_tripping=0.0000,
            ),
        ),
        (
            'Concept N Class',
            dict(
                design_score=HighMediumLow.MEDIUM,
                topside_design=TopsideDesign.NOV,
                derrick_height_ft=180.0000,
                mudpump_qty=3.0000,
                liquid_mud_bbl=7220.0000,
                mud_total_hp=6600.0000,
                offline_stand_building=False,
                auto_pipe_handling=False,
                dual_activity=False,
                drilltronic=False,
                dynamic_drilling_guide=False,
                process_automation_platform=False,
                automatic_tripping=False,
            ),
            JackupTopsideEfficiencyResult(
                points=15.25795039552727,
                design_score=1.0000,
                topside_design=1.0300,
                derrick_height_ft=2.1176470588235294,
                mudpump_qty=3.0600,
                liquid_mud_bbl=7.300303336703741,
                mud_total_hp=0.7500,
                offline_stand_building=0.0000,
                auto_pipe_handling=0.0000,
                dual_activity=0.0000,
                drilltronic=0.0000,
                dynamic_drilling_guide=0.0000,
                process_automation_platform=0.0000,
                automatic_tripping=0.0000,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                design_score=HighMediumLow.MEDIUM,
                topside_design=TopsideDesign.NOV,
                derrick_height_ft=170.0000,
                mudpump_qty=4.0000,
                liquid_mud_bbl=5566.0000,
                mud_total_hp=8800.0000,
                offline_stand_building=False,
                auto_pipe_handling=False,
                dual_activity=False,
                drilltronic=False,
                dynamic_drilling_guide=False,
                process_automation_platform=False,
                automatic_tripping=False,
            ),
            JackupTopsideEfficiencyResult(
                points=14.737906976744185,
                design_score=1.0000,
                topside_design=1.0300,
                derrick_height_ft=2.0000,
                mudpump_qty=4.0800,
                liquid_mud_bbl=5.627906976744186,
                mud_total_hp=1.0000,
                offline_stand_building=0.0000,
                auto_pipe_handling=0.0000,
                dual_activity=0.0000,
                drilltronic=0.0000,
                dynamic_drilling_guide=0.0000,
                process_automation_platform=0.0000,
                automatic_tripping=0.0000,
            ),
        ),
    ),
)
def test_calculate_jackup_topside_efficiency(name, input, output):
    result = calculate_jackup_topside_efficiency(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_reference_jackup_topside_efficiency():
    assert calculate_reference_jackup_topside_efficiency()['points'] == 22.4020486176822


@pytest.mark.django_db
def test_calculate_custom_jackup_topside_efficiency(concept_cj70):
    assert calculate_custom_jackup_topside_efficiency(concept_cj70) == JackupTopsideEfficiencyResult(
        points=22.4020486176822,
        design_score=1.0000,
        topside_design=1.0300,
        derrick_height_ft=2.4705882352941178,
        mudpump_qty=3.0600,
        liquid_mud_bbl=10.070778564206268,
        mud_total_hp=0.8806818181818182,
        offline_stand_building=1.9800,
        auto_pipe_handling=1.9100,
        dual_activity=0.0000,
        drilltronic=0.0000,
        dynamic_drilling_guide=0.0000,
        process_automation_platform=0.0000,
        automatic_tripping=0.0000,
    )


@pytest.mark.django_db
def test_calculate_custom_jackup_topside_efficiency_score(concept_cj70):
    assert calculate_custom_jackup_topside_efficiency_score(concept_cj70) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                topside_design=TopsideDesign.NOV,
                variable_load_t=12509.6363636364,
                cantilever_reach_ft=104.545454545455,
                cantilever_lateral_ft=35.8181818181818,
                total_cranes=3.0000,
                crane_capacity=85.0000,
                hull_breadth_ft=320.0000,
                hull_depth_ft=40.0000,
                hull_length_ft=310.0000,
                auto_pipe_handling=True,
            ),
            JackupDeckEfficiencyResult(
                points=35.662663888227414,
                topside_design=1.0500,
                variable_load_t=6.2548181818182,
                cantilever_reach_ft=11.004784688995263,
                cantilever_lateral_ft=7.023172905525843,
                total_cranes=2.727272727272727,
                crane_capacity=1.6346153846153846,
                vessel_size=3.9680,
                auto_pipe_handling=2.0000,
            ),
        ),
        (
            'Concept CJ62',
            dict(
                topside_design=TopsideDesign.NOV,
                variable_load_t=4346.5000,
                cantilever_reach_ft=61.5000,
                cantilever_lateral_ft=15.0000,
                total_cranes=2.0000,
                crane_capacity=52.5000,
                hull_breadth_ft=296.0000,
                hull_depth_ft=35.0000,
                hull_length_ft=256.0000,
                auto_pipe_handling=False,
            ),
            JackupDeckEfficiencyResult(
                points=18.118067883911753,
                topside_design=1.0500,
                variable_load_t=2.17325,
                cantilever_reach_ft=6.473684210526316,
                cantilever_lateral_ft=2.9411764705882355,
                total_cranes=1.8181818181818181,
                crane_capacity=1.0096153846153846,
                vessel_size=2.65216,
                auto_pipe_handling=0.0000,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                topside_design=TopsideDesign.NOV,
                variable_load_t=4955.0000,
                cantilever_reach_ft=70.0000,
                cantilever_lateral_ft=23.0000,
                total_cranes=2.0000,
                crane_capacity=88.0000,
                hull_breadth_ft=223.0000,
                hull_depth_ft=31.0000,
                hull_length_ft=229.0000,
                auto_pipe_handling=False,
            ),
            JackupDeckEfficiencyResult(
                points=20.499291484689717,
                topside_design=1.0500,
                variable_load_t=2.4775,
                cantilever_reach_ft=7.368421052631579,
                cantilever_lateral_ft=4.509803921568627,
                total_cranes=1.8181818181818181,
                crane_capacity=1.6923076923076923,
                vessel_size=1.583077,
                auto_pipe_handling=0.0000,
            ),
        ),
        (
            'Concept N Class',
            dict(
                topside_design=TopsideDesign.NOV,
                variable_load_t=4177.33333333333,
                cantilever_reach_ft=75.0000,
                cantilever_lateral_ft=20.0000,
                total_cranes=3.0000,
                crane_capacity=88.0000,
                hull_breadth_ft=289.0000,
                hull_depth_ft=35.0000,
                hull_length_ft=264.0000,
                auto_pipe_handling=False,
            ),
            JackupDeckEfficiencyResult(
                points=22.04491255580333,
                topside_design=1.0500,
                variable_load_t=2.0886666666666653,
                cantilever_reach_ft=7.894736842105263,
                cantilever_lateral_ft=3.9215686274509807,
                total_cranes=2.727272727272727,
                crane_capacity=1.6923076923076923,
                vessel_size=2.67036,
                auto_pipe_handling=0.0000,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                topside_design=TopsideDesign.NOV,
                variable_load_t=6231.0000,
                cantilever_reach_ft=100.0000,
                cantilever_lateral_ft=20.0000,
                total_cranes=5.0000,
                crane_capacity=75.0000,
                hull_breadth_ft=300.0000,
                hull_depth_ft=36.0000,
                hull_length_ft=306.0000,
                auto_pipe_handling=False,
            ),
            JackupDeckEfficiencyResult(
                points=27.905946654686907,
                topside_design=1.0500,
                variable_load_t=3.1155,
                cantilever_reach_ft=10.526315789473685,
                cantilever_lateral_ft=3.9215686274509807,
                total_cranes=4.545454545454545,
                crane_capacity=1.4423076923076923,
                vessel_size=3.3048,
                auto_pipe_handling=0.0000,
            ),
        ),
    ),
)
def test_calculate_jackup_deck_efficiency(name, input, output):
    result = calculate_jackup_deck_efficiency(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_reference_jackup_deck_efficiency():
    assert calculate_reference_jackup_deck_efficiency()['points'] == 35.662663888227414


@pytest.mark.django_db
def test_calculate_custom_jackup_deck_efficiency(concept_cj70):
    assert calculate_custom_jackup_deck_efficiency(concept_cj70) == JackupDeckEfficiencyResult(
        points=35.662663888227414,
        topside_design=1.0500,
        variable_load_t=6.2548181818182,
        cantilever_reach_ft=11.004784688995263,
        cantilever_lateral_ft=7.023172905525843,
        total_cranes=2.727272727272727,
        crane_capacity=1.6346153846153846,
        vessel_size=3.9680,
        auto_pipe_handling=2.0000,
    )


@pytest.mark.django_db
def test_calculate_custom_jackup_deck_efficiency_score(concept_cj70):
    assert calculate_custom_jackup_deck_efficiency_score(concept_cj70) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                quarters_capacity=145.0000,
                rig_water_depth_ft=490.0000,
                variable_load_t=12509.6363636364,
                cantilever_reach_ft=104.545454545455,
                cantilever_lateral_ft=35.8181818181818,
                cantilever_capacity_lbs=3114717.09090909,
                derrick_height_ft=210.0000,
                total_bop_rams=4.0000,
                bop_diameter_wp_max_in=18.7500,
                mudpump_qty=3.0000,
                liquid_mud_bbl=9960.0000,
                subsea_drilling=True,
                enhanced_legs=False,
                closed_bus=False,
                hybrid=False,
            ),
            JackupCapacitiesResult(
                points=28.873988861244033,
                quarters_capacity=1.4500,
                rig_water_depth_ft=1.9600,
                variable_load_t=2.50192727272728,
                cantilever_reach_ft=2.0909090909091,
                cantilever_lateral_ft=1.79090909090909,
                cantilever_capacity_lbs=3.1147170909090898,
                derrick_height_ft=1.0500,
                total_bop_rams=4.2105263157894735,
                bop_diameter_wp_max_in=1.8750,
                mudpump_qty=2.8499999999999996,
                liquid_mud_bbl=4.9800,
                subsea_drilling=1.0000,
                enhanced_legs=0.0000,
                closed_bus=0.0000,
                hybrid=0.0000,
            ),
        ),
        (
            'Concept CJ62',
            dict(
                quarters_capacity=118.0000,
                rig_water_depth_ft=390.0000,
                variable_load_t=4346.5000,
                cantilever_reach_ft=61.5000,
                cantilever_lateral_ft=15.0000,
                cantilever_capacity_lbs=1760000.0000,
                derrick_height_ft=160.0000,
                total_bop_rams=4.0000,
                bop_diameter_wp_max_in=16.1875,
                mudpump_qty=3.0000,
                liquid_mud_bbl=5190.0000,
                subsea_drilling=False,
                enhanced_legs=False,
                closed_bus=False,
                hybrid=False,
            ),
            JackupCapacitiesResult(
                points=19.42357631578947,
                quarters_capacity=1.1800,
                rig_water_depth_ft=1.5600,
                variable_load_t=0.8693,
                cantilever_reach_ft=1.2300,
                cantilever_lateral_ft=0.7500,
                cantilever_capacity_lbs=1.7600,
                derrick_height_ft=0.8000,
                total_bop_rams=4.2105263157894735,
                bop_diameter_wp_max_in=1.61875,
                mudpump_qty=2.8499999999999996,
                liquid_mud_bbl=2.5950,
                subsea_drilling=0.0000,
                enhanced_legs=0.0000,
                closed_bus=0.0000,
                hybrid=0.0000,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                quarters_capacity=120.0000,
                rig_water_depth_ft=350.0000,
                variable_load_t=4955.0000,
                cantilever_reach_ft=70.0000,
                cantilever_lateral_ft=23.0000,
                cantilever_capacity_lbs=2645547.0000,
                derrick_height_ft=210.0000,
                total_bop_rams=4.0000,
                bop_diameter_wp_max_in=18.7500,
                mudpump_qty=3.0000,
                liquid_mud_bbl=6290.0000,
                subsea_drilling=False,
                enhanced_legs=False,
                closed_bus=False,
                hybrid=False,
            ),
            JackupCapacitiesResult(
                points=21.917073315789477,
                quarters_capacity=1.2000,
                rig_water_depth_ft=1.4000,
                variable_load_t=0.9910,
                cantilever_reach_ft=1.4000,
                cantilever_lateral_ft=1.1500,
                cantilever_capacity_lbs=2.645547,
                derrick_height_ft=1.0500,
                total_bop_rams=4.2105263157894735,
                bop_diameter_wp_max_in=1.8750,
                mudpump_qty=2.8499999999999996,
                liquid_mud_bbl=3.1450,
                subsea_drilling=0.0000,
                enhanced_legs=0.0000,
                closed_bus=0.0000,
                hybrid=0.0000,
            ),
        ),
        (
            'Concept N Class',
            dict(
                quarters_capacity=120.0000,
                rig_water_depth_ft=410.0000,
                variable_load_t=4177.3333,
                cantilever_reach_ft=75.0000,
                cantilever_lateral_ft=20.0000,
                cantilever_capacity_lbs=3000000.0000,
                derrick_height_ft=180.0000,
                total_bop_rams=4.0000,
                bop_diameter_wp_max_in=18.7500,
                mudpump_qty=3.0000,
                liquid_mud_bbl=7220.0000,
                subsea_drilling=False,
                enhanced_legs=False,
                closed_bus=False,
                hybrid=False,
            ),
            JackupCapacitiesResult(
                points=22.62099297578947,
                quarters_capacity=1.2000,
                rig_water_depth_ft=1.6400,
                variable_load_t=0.83546666,
                cantilever_reach_ft=1.5000,
                cantilever_lateral_ft=1.0000,
                cantilever_capacity_lbs=3.0000,
                derrick_height_ft=0.9000,
                total_bop_rams=4.2105263157894735,
                bop_diameter_wp_max_in=1.8750,
                mudpump_qty=2.8499999999999996,
                liquid_mud_bbl=3.6100,
                subsea_drilling=0.0000,
                enhanced_legs=0.0000,
                closed_bus=0.0000,
                hybrid=0.0000,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                quarters_capacity=120.0000,
                rig_water_depth_ft=400.0000,
                variable_load_t=6231.0000,
                cantilever_reach_ft=100.0000,
                cantilever_lateral_ft=20.0000,
                cantilever_capacity_lbs=1875000.0000,
                derrick_height_ft=170.0000,
                total_bop_rams=4.0000,
                bop_diameter_wp_max_in=18.7500,
                mudpump_qty=4.0000,
                liquid_mud_bbl=5566.0000,
                subsea_drilling=False,
                enhanced_legs=False,
                closed_bus=False,
                hybrid=False,
            ),
            JackupCapacitiesResult(
                points=22.439726315789475,
                quarters_capacity=1.2000,
                rig_water_depth_ft=1.6000,
                variable_load_t=1.2462,
                cantilever_reach_ft=2.0000,
                cantilever_lateral_ft=1.0000,
                cantilever_capacity_lbs=1.8750,
                derrick_height_ft=0.8500,
                total_bop_rams=4.2105263157894735,
                bop_diameter_wp_max_in=1.8750,
                mudpump_qty=3.8000,
                liquid_mud_bbl=2.7830,
                subsea_drilling=0.0000,
                enhanced_legs=0.0000,
                closed_bus=0.0000,
                hybrid=0.0000,
            ),
        ),
    ),
)
def test_calculate_jackup_capacities(name, input, output):
    result = calculate_jackup_capacities(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_reference_jackup_capacities():
    assert calculate_reference_jackup_capacities()['points'] == 28.873988861244033


@pytest.mark.django_db
def test_calculate_custom_jackup_capacities(concept_cj70):
    assert calculate_custom_jackup_capacities(concept_cj70) == JackupCapacitiesResult(
        points=28.873988861244033,
        quarters_capacity=1.4500,
        rig_water_depth_ft=1.9600,
        variable_load_t=2.50192727272728,
        cantilever_reach_ft=2.0909090909091,
        cantilever_lateral_ft=1.79090909090909,
        cantilever_capacity_lbs=3.1147170909090898,
        derrick_height_ft=1.0500,
        total_bop_rams=4.2105263157894735,
        bop_diameter_wp_max_in=1.8750,
        mudpump_qty=2.8499999999999996,
        liquid_mud_bbl=4.9800,
        subsea_drilling=1.0000,
        enhanced_legs=0.0000,
        closed_bus=0.0000,
        hybrid=0.0000,
    )


@pytest.mark.django_db
def test_calculate_custom_jackup_capacities_score(concept_cj70):
    assert calculate_custom_jackup_capacities_score(concept_cj70) == 1


@pytest.mark.django_db
def test_calculate_jackup_move():
    assert calculate_jackup_move(
        co2_score=1,
        number_of_tugs=3,
        tug_boat_move_fuel_consumption_td=22,
        move_distance_nm=10,
        move_speed_kn=2.5,
        positioning_time_d=1.5,
        tug_boat_transit_to_rig_distance_nm=100,
        tug_boat_return_distance_nm=90,
        tug_boat_transit_speed_kn=12,
        tug_boat_transit_fuel_consumption_td=12,
        jack_up_time_d=1.4,
        jack_down_time_d=1.4,
    ) == JackupMoveResult(
        fuel_td=5.0000,
        move_time_d=0.16666666666666666,
        tug_to_field_and_return_time_d=0.6597222222222222,
        total_move_time_d=4.466666666666667,
        total_fuel_t=156.08333333333334,
    )


@pytest.mark.django_db
class TestCalculateCustomJackupMove:
    @pytest.fixture()
    def project(self):
        return ProjectFactory(
            tugs_avg_move_fuel_consumption=22,
            tugs_avg_transit_fuel_consumption=12,
            tugs_transit_speed=12,
            tugs_move_speed=2.5,
        )

    @pytest.fixture()
    def jackup_move_result(self):
        return JackupMoveResult(
            fuel_td=5.0,
            move_time_d=0.16666666666666666,
            tug_to_field_and_return_time_d=0.6597222222222222,
            total_move_time_d=4.466666666666667,
            total_fuel_t=156.08333333333334,
        )

    def test_calculate_move_for_first_well(self, project, concept_cj70, jackup_move_result):
        concept_cj70.project = project
        concept_cj70.save()
        plan = PlanFactory(
            project=project,
            distance_from_tug_base_to_previous_well=100,
        )
        PlanWellRelationFactory(
            plan=plan,
            distance_to_tug_base=90,
            distance_from_previous_location=10,
            jackup_positioning_time=1.5,
        )
        assert calculate_custom_jackup_move(rig=concept_cj70, plan=plan, well_index=0) == jackup_move_result

    def test_calculate_move_for_second_well(self, project, concept_cj70, jackup_move_result):
        concept_cj70.project = project
        concept_cj70.save()
        plan = PlanFactory(
            project=project,
            distance_from_tug_base_to_previous_well=200,
        )
        PlanWellRelationFactory(
            plan=plan,
            distance_to_tug_base=100,
            distance_from_previous_location=33,
            jackup_positioning_time=1.2,
            order=1,
        )
        PlanWellRelationFactory(
            plan=plan,
            distance_to_tug_base=90,
            distance_from_previous_location=10,
            jackup_positioning_time=1.5,
            order=2,
        )
        assert calculate_custom_jackup_move(rig=concept_cj70, plan=plan, well_index=1) == jackup_move_result


@pytest.mark.django_db
def test_calculate_reference_jackup_rig_status():
    assert calculate_reference_jackup_rig_status()['points'] == 23.0


@pytest.mark.django_db
def test_calculate_custom_jackup_rig_status_score(concept_cj70):
    assert calculate_custom_jackup_rig_status_score(concept_cj70) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                deck_efficiency=1,
                co2_efficiency=1.0000,
                fuel_density_tm3=0.85,
                co2_emission_per_tonne_fuel=3.17,
                operational_days=62.0000,
                move_time=4.4666666667,
                psv_visits_per_7_days=1.5,
                psv_fuel_per_trip=9.7083333333,
                psv_time_per_trip_d=0.9444444444,
                psv_day_rate=12000.0000,
                psv_fuel_cost_usd_t=2000.0000,
                helicopter_trips_per_7_days=1.5000,
                helicopter_factor=1.0550,
                helicopter_fuel_consumption_per_trip_t=0.9166666667,
                helicopter_fuel_cost_usd_t=2000.0000,
                helicopter_charter_price_usd=10000.0000,
                move_fuel=157.3333333333,
                tugs_day_rate=4500,
                total_fuel_price=1120,
                rig_day_rate_usd_d=300000.0000,
                rig_spread_cost=300000.0000,
                number_of_tugs=3,
                helicopter_co2_emission_per_tonne_fuel=3.16,
            ),
            JackupCO2PerWellResult(
                fuel=19.679347826086953,
                co2_td=62.38353260869564,
                fuel_winter=20.269728260869563,
                co2_winter_td=64.25503858695652,
                fuel_summer=19.088967391304344,
                co2_summer_td=60.51202663043477,
                operational_days=62.0000,
                move_time=4.4666666667,
                total_days=66.46666666670001,
                rig_day_rate_usd_d=300000.0000,
                spread_cost=300000.0000,
                fuel_per_day=19.679347826086953,
                co2=62.38353260869564,
                psv_trips=14.242857142864287,
                psv_fuel=138.27440476149937,
                psv_co2=438.329863093953,
                psv_cost_usd=437967.85713453114,
                helicopter_trips=15.02621428572182,
                helicopter_fuel=13.774029762412543,
                helicopter_co2=43.525934049223636,
                helicopter_cost_usd=177810.2023820433,
                move_fuel=157.3333333333,
                tugs=3.0000,
                tugs_cost=13500.0000,
                total_fuel=1529.5013330746028,
                total_co2=4848.381485548867,
                total_cost=42052025.30591335,
            ),
        ),
        (
            'Concept CJ62',
            dict(
                deck_efficiency=0.5080402277,
                co2_efficiency=0.7861000647,
                fuel_density_tm3=0.85,
                co2_emission_per_tonne_fuel=3.17,
                operational_days=71.0700765495,
                move_time=4.4666666667,
                psv_visits_per_7_days=1.5,
                psv_fuel_per_trip=9.7083333333,
                psv_time_per_trip_d=0.9444444444,
                psv_day_rate=12000.0000,
                psv_fuel_cost_usd_t=2000.0000,
                helicopter_trips_per_7_days=1.5000,
                helicopter_factor=1.0820,
                helicopter_fuel_consumption_per_trip_t=0.9166666667,
                helicopter_fuel_cost_usd_t=2000.0000,
                helicopter_charter_price_usd=10000.0000,
                move_fuel=135.8895681117,
                tugs_day_rate=4500,
                total_fuel_price=1120,
                rig_day_rate_usd_d=300000.0000,
                rig_spread_cost=300000.0000,
                number_of_tugs=3,
                helicopter_co2_emission_per_tonne_fuel=3.16,
            ),
            JackupCO2PerWellResult(
                fuel=15.469936599340759,
                co2_td=49.0396990199102,
                fuel_winter=15.934034697320982,
                co2_winter_td=50.510889990507515,
                fuel_summer=15.005838501360536,
                co2_summer_td=47.568508049312896,
                operational_days=71.0700765495,
                move_time=4.4666666667,
                total_days=75.5367432162,
                rig_day_rate_usd_d=300000.0000,
                spread_cost=300000.0000,
                fuel_per_day=15.469936599340759,
                co2=49.0396990199102,
                psv_co2=612.5092343298697,
                psv_cost_usd=612003.3778694789,
                psv_fuel=193.22057865295577,
                psv_trips=19.902548874192533,
                helicopter_co2=50.73144793254319,
                helicopter_cost_usd=207245.84597812887,
                helicopter_fuel=16.05425567485544,
                helicopter_trips=17.5137334628418,
                move_fuel=135.8895681117,
                tugs=3.0000,
                tugs_cost=13500.0000,
                total_fuel=1444.6139807705706,
                total_co2=4579.26577648596,
                total_cost=47538374.99758349,
            ),
        ),
        (
            'Concept CJ50',
            dict(
                deck_efficiency=0.5748109998,
                co2_efficiency=0.8830959470,
                fuel_density_tm3=0.85,
                co2_emission_per_tonne_fuel=3.17,
                operational_days=68.0812113573,
                move_time=4.4666666667,
                psv_visits_per_7_days=1.5,
                psv_fuel_per_trip=9.7083333333,
                psv_time_per_trip_d=0.9444444444,
                psv_day_rate=12000.0000,
                psv_fuel_cost_usd_t=2000.0000,
                helicopter_trips_per_7_days=1.5000,
                helicopter_factor=1.0800,
                helicopter_fuel_consumption_per_trip_t=0.9166666667,
                helicopter_fuel_cost_usd_t=2000.0000,
                helicopter_charter_price_usd=10000.0000,
                move_fuel=138.0558094839,
                tugs_day_rate=4500,
                total_fuel_price=1120,
                rig_day_rate_usd_d=300000.0000,
                rig_spread_cost=300000.0000,
                number_of_tugs=3,
                helicopter_co2_emission_per_tonne_fuel=3.16,
            ),
            JackupCO2PerWellResult(
                fuel=17.37875230482065,
                co2_td=55.09064480628146,
                fuel_winter=17.900114873965272,
                co2_winter_td=56.74336415046991,
                fuel_summer=16.85738973567603,
                co2_summer_td=53.43792546209301,
                operational_days=68.0812113573,
                move_time=4.4666666667,
                total_days=72.547878024,
                rig_day_rate_usd_d=300000.0000,
                spread_cost=300000.0000,
                fuel_per_day=17.37875230482065,
                co2=55.09064480628146,
                psv_co2=573.365395921857,
                psv_cost_usd=572891.86740435,
                psv_fuel=180.87236464411896,
                psv_trips=18.630629834651327,
                helicopter_co2=48.634024632543145,
                helicopter_cost_usd=198677.54596113076,
                helicopter_fuel=15.390514124222513,
                helicopter_trips=16.789651771268574,
                move_fuel=138.0558094839,
                tugs=3.0000,
                tugs_cost=13500.0000,
                total_fuel=1517.4851970429008,
                total_co2=4810.274169484754,
                total_cost=45793565.224232994,
            ),
        ),
        (
            'Concept N Class',
            dict(
                deck_efficiency=0.6181510339,
                co2_efficiency=0.8928487950,
                fuel_density_tm3=0.85,
                co2_emission_per_tonne_fuel=3.17,
                operational_days=67.9830881578,
                move_time=4.4666666667,
                psv_visits_per_7_days=1.5,
                psv_fuel_per_trip=9.7083333333,
                psv_time_per_trip_d=0.9444444444,
                psv_day_rate=12000.0000,
                psv_fuel_cost_usd_t=2000.0000,
                helicopter_trips_per_7_days=1.5000,
                helicopter_factor=1.0800,
                helicopter_fuel_consumption_per_trip_t=0.9166666667,
                helicopter_fuel_cost_usd_t=2000.0000,
                helicopter_charter_price_usd=10000.0000,
                move_fuel=138.2736230874,
                tugs_day_rate=4500,
                total_fuel_price=1120,
                rig_day_rate_usd_d=300000.0000,
                rig_spread_cost=300000.0000,
                number_of_tugs=3,
                helicopter_co2_emission_per_tonne_fuel=3.16,
            ),
            JackupCO2PerWellResult(
                fuel=17.570681992907605,
                co2_td=55.699061917517106,
                fuel_winter=18.097802452694832,
                co2_winter_td=57.370033775042614,
                fuel_summer=17.04356153312038,
                co2_summer_td=54.0280900599916,
                operational_days=67.9830881578,
                move_time=4.4666666667,
                total_days=72.44975482449999,
                rig_day_rate_usd_d=300000.0000,
                spread_cost=300000.0000,
                fuel_per_day=17.570681992907605,
                co2=55.699061917517106,
                psv_co2=562.9264984637637,
                psv_cost_usd=562461.591177452,
                psv_fuel=177.57933705481503,
                psv_trips=18.29143385978624,
                helicopter_co2=48.56824564311593,
                helicopter_cost_usd=198408.8285704985,
                helicopter_fuel=15.369697988327825,
                helicopter_trips=16.766943259384284,
                move_fuel=138.2736230874,
                tugs=3.0000,
                tugs_cost=13500.0000,
                total_fuel=1525.7318810470495,
                total_co2=4836.416365939263,
                total_cost=45736940.10197231,
            ),
        ),
        (
            'Concept Super Gorilla',
            dict(
                deck_efficiency=0.7824975370,
                co2_efficiency=0.8828888932,
                fuel_density_tm3=0.85,
                co2_emission_per_tonne_fuel=3.17,
                operational_days=68.07485873190001,
                move_time=4.4666666667,
                psv_visits_per_7_days=1.5,
                psv_fuel_per_trip=9.7083333333,
                psv_time_per_trip_d=0.9444444444,
                psv_day_rate=12000.0000,
                psv_fuel_cost_usd_t=2000.0000,
                helicopter_trips_per_7_days=1.5000,
                helicopter_factor=1.0800,
                helicopter_fuel_consumption_per_trip_t=0.9166666667,
                helicopter_fuel_cost_usd_t=2000.0000,
                helicopter_charter_price_usd=10000.0000,
                move_fuel=138.0511852816,
                tugs_day_rate=4500,
                total_fuel_price=1120,
                rig_day_rate_usd_d=300000.0000,
                rig_spread_cost=300000.0000,
                number_of_tugs=3,
                helicopter_co2_emission_per_tonne_fuel=3.16,
            ),
            JackupCO2PerWellResult(
                fuel=17.374677621071736,
                co2_td=55.077728058797405,
                fuel_winter=17.89591794970389,
                co2_winter_td=56.73005990056133,
                fuel_summer=16.853437292439583,
                co2_summer_td=53.42539621703348,
                operational_days=68.07485873190001,
                move_time=4.4666666667,
                total_days=72.54152539860002,
                rig_day_rate_usd_d=300000.0000,
                spread_cost=300000.0000,
                fuel_per_day=17.374677621071736,
                co2=55.077728058797405,
                psv_co2=526.9492599175701,
                psv_cost_usd=526514.0653564315,
                psv_fuel=166.230050447183,
                psv_trips=17.122408629811545,
                helicopter_co2=48.629766013978426,
                helicopter_cost_usd=198660.14884271385,
                helicopter_fuel=15.389166460119753,
                helicopter_trips=16.788181592247433,
                move_fuel=138.0511852816,
                tugs=3.0000,
                tugs_cost=13500.0000,
                total_fuel=1502.4491267556657,
                total_co2=4762.609840150859,
                total_cost=45742918.95238932,
            ),
        ),
    ),
)
def test_calculate_jackup_co2_per_well(name, input, output):
    result = calculate_jackup_co2_per_well(**input)

    assert result == output


@pytest.mark.django_db
def test_calculate_custom_jackup_co2_per_well(concept_cj70):
    project = ProjectFactory(
        fuel_density=0.85,
        co2_emission_per_tonne_fuel=3.17,
        fuel_total_price=1120.0000,
        tugs_day_rate=4500,
        tugs_avg_move_fuel_consumption=22,
        tugs_avg_transit_fuel_consumption=12,
        tugs_transit_speed=12,
        tugs_move_speed=2.5,
        psv_calls_per_week=1.5,
        psv_day_rate=12000.0000,
        psv_speed=12,
        psv_avg_fuel_transit_consumption=12.0000,
        psv_avg_fuel_dp_consumption=5.5000,
        psv_loading_time=0.2500,
        psv_fuel_price=2000,
        helicopter_no_flights_per_week=1.5000,
        helicopter_rate_per_trip=10000.0000,
        helicopter_avg_fuel_consumption=12.0000,
        helicopter_fuel_price=2000,
        helicopter_cruise_speed=120.000,
    )
    concept_cj70.project = project
    concept_cj70.save()
    plan = PlanFactory(
        project=project,
        reference_operation_jackup=concept_cj70,
        distance_from_tug_base_to_previous_well=100,
    )
    plan_well = PlanWellRelationFactory(
        plan=plan,
        distance_to_tug_base=100,
        distance_from_previous_location=10,
        distance_to_helicopter_base=110.0000,
        distance_to_psv_base=100.0000,
        jackup_positioning_time=1.5,
        operational_time=62,
    )
    assert calculate_custom_jackup_co2_per_well(
        plan=plan,
        plan_well=plan_well,
        well_index=0,
        rig=concept_cj70,
    ) == JackupCO2PerWellResult(
        fuel=19.679347826086953,
        co2_td=62.38353260869564,
        fuel_winter=20.269728260869563,
        co2_winter_td=64.25503858695652,
        fuel_summer=19.088967391304344,
        co2_summer_td=60.51202663043477,
        operational_days=62.0000,
        move_time=4.466666666666667,
        total_days=66.46666666666667,
        rig_day_rate_usd_d=300000.0000,
        spread_cost=300000.0000,
        fuel_per_day=19.679347826086953,
        co2=62.38353260869564,
        psv_co2=438.3298630952381,
        psv_cost_usd=437967.85714285716,
        psv_fuel=138.27440476190478,
        psv_trips=14.242857142857144,
        helicopter_co2=43.525934047619046,
        helicopter_cost_usd=177810.2023809524,
        helicopter_fuel=13.77402976190476,
        helicopter_trips=15.026214285714286,
        move_fuel=157.33333333333334,
        tugs=3.0000,
        tugs_cost=13500.0000,
        total_fuel=1529.501333074534,
        total_co2=4848.3814855486535,
        total_cost=42052025.305900626,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                efficiency=1.0000000000,
                reference_operational_days=62,
            ),
            62.0000,
        ),
        (
            'Concept CJ62',
            dict(
                efficiency=0.7074168855,
                reference_operational_days=62,
            ),
            71.0700765495,
        ),
        (
            'Concept CJ50',
            dict(
                efficiency=0.8038318917,
                reference_operational_days=62,
            ),
            68.0812113573,
        ),
        (
            'Concept N Class',
            dict(
                efficiency=0.8069971562,
                reference_operational_days=62,
            ),
            67.9830881578,
        ),
        (
            'Concept Super Gorilla',
            dict(
                efficiency=0.8040368151,
                reference_operational_days=62,
            ),
            68.07485873190001,
        ),
    ),
)
def test_calculate_jackup_well_operational_days(name, input, output):
    result = calculate_jackup_well_operational_days(**input)

    assert result == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Concept CJ70',
            dict(
                efficiency=1.0000000000,
                operational_days=62.0000,
            ),
            62,
        ),
        (
            'Concept CJ62',
            dict(
                efficiency=0.7074168855,
                operational_days=71.0700765495,
            ),
            61.99999999999999,
        ),
        (
            'Concept CJ50',
            dict(
                efficiency=0.8038318917,
                operational_days=68.0812113573,
            ),
            62,
        ),
        (
            'Concept N Class',
            dict(
                efficiency=0.8069971562,
                operational_days=67.9830881578,
            ),
            62,
        ),
        (
            'Concept Super Gorilla',
            dict(
                efficiency=0.8040368151,
                operational_days=68.07485873190001,
            ),
            62.00000000000001,
        ),
    ),
)
def test_calculate_jackup_well_reference_operational_days(name, input, output):
    result = calculate_jackup_well_reference_operational_days(**input)

    assert result == output


@pytest.mark.django_db
class TestCalculateCustomJackupWellOperationalDays:
    def test_calculate_well_operational_days_for_reference_rig(self):
        custom_rig = CustomJackupRigFactory()
        plan = PlanFactory(
            reference_operation_jackup=custom_rig,
        )
        plan_well = PlanWellRelationFactory(plan=plan, operational_time=62)

        assert (
            calculate_custom_jackup_well_operational_days(plan=plan, plan_well=plan_well, rig=custom_rig)
            == plan_well.operational_time
        )

    def test_calculate_well_operational_days_for_custom_rig(self, concept_cj70):
        custom_cj70 = CustomJackupRig.objects.get(pk=concept_cj70.pk)
        custom_cj70.emp = None
        custom_cj70.pk = None
        custom_cj70.save()
        plan = PlanFactory(
            reference_operation_jackup=concept_cj70,
        )
        plan_well = PlanWellRelationFactory(plan=plan, operational_time=62)
        assert concept_cj70.pk != custom_cj70.pk
        assert (
            calculate_custom_jackup_well_operational_days(plan=plan, plan_well=plan_well, rig=custom_cj70)
            == plan_well.operational_time
        )
