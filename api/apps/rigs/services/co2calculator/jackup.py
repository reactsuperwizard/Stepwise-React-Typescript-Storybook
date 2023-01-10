import datetime
import logging
from typing import TypedDict

from apps.projects.models import Plan, PlanWellRelation
from apps.rigs.models import CustomJackupRig, CustomJackupSubareaScore, HighMediumLow, RigStatus, TopsideDesign
from apps.rigs.services.co2calculator.common import (
    HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL,
    RigStatusResult,
    calculate_custom_helicopter,
    calculate_custom_psv,
    calculate_custom_rig_status,
    calculate_rig_status,
    calculate_well_reference_operational_days,
)

logger = logging.getLogger(__name__)


class JackupCO2Result(TypedDict):
    points: float
    vessel_size: float
    accommodation: float
    generator_sets_score: float
    generator_set_hp_average: float
    engine_sets_score: float
    engine_set_hp_average: float
    mudpumps_hp_total: float
    drawworks_hp: float
    hybrid: float
    closed_bus: float
    hvac_heat_recovery: float
    freshwater_cooling_systems: float
    seawater_cooling_systems: float
    operator_awareness_dashboard: float
    hpu_optimization: float
    optimized_heat_tracing_system: float
    floodlighting_optimization: float
    vfds_on_aux_machinery: float


def calculate_jackup_co2(
    *,
    # 'JU NCS database'!Y
    hull_breadth_ft: float,
    # 'JU NCS database'!Z
    hull_depth_ft: float,
    # 'JU NCS database'!AA
    hull_length_ft: float,
    # 'JU NCS database'!N
    quarters_capacity: float,
    # 'JU NCS database'!AP
    generator_qty_1: float,
    # 'JU NCS database'!AM
    engine_qty_1: float,
    # 'JU NCS database'!AJ
    mud_total_hp: float,
    # 'JU NCS database'!V
    drawworks_hp: float,
    # 'JU NCS database'!BC
    hybrid: bool,
    # 'JU NCS database'!BA
    closed_bus: bool,
    # ('JU NCS database'!AO)
    generator_kw_1: float,
    # 'JU NCS database'!AL
    engine_hp_1: float,
    # 'JU NCS database'!BD
    hvac_heat_recovery: bool,
    # 'JU NCS database'!BE
    freshwater_cooling_systems: bool,
    # 'JU NCS database'!BF
    seawater_cooling_systems: bool,
    # 'JU NCS database'!BG
    operator_awareness_dashboard: bool,
    # 'JU NCS database'!BH
    hpu_optimization: bool,
    # 'JU NCS database'!BI
    optimized_heat_tracing_system: bool,
    # 'JU NCS database'!BJ
    floodlighting_optimization: bool,
    # 'JU NCS database'!BK
    vfds_on_aux_machinery: bool,
) -> JackupCO2Result:
    logger.info('Calculating Jackup CO2')
    # =('JU NCS database'!Y*'JU NCS database'!Z*'JU NCS database'!AA)/1000000
    vessel_size_score = (hull_breadth_ft * hull_depth_ft * hull_length_ft) / 1000000
    # ='JU NCS database'!N/15
    accommodation_score = quarters_capacity / 15
    # =10-('JU NCS database'!AP)
    generator_sets_score = 10.0 - generator_qty_1
    # =('JU NCS database'!AO)/1000
    generator_set_hp_average_score = generator_kw_1 / 1000
    # =10-('JU NCS database'!AM)
    engine_sets_score = 10 - engine_qty_1
    # =('JU NCS database'!AL)/1000
    engine_set_hp_average_score = engine_hp_1 / 1000
    # ='JU NCS database'!AJ/1000
    mudpumps_hp_total_score = mud_total_hp / 1000
    # ='JU NCS database'!V/1000
    drawworks_hp_score = drawworks_hp / 1000
    # =IFS('JU NCS database'!BC="Y";0;TRUE;3)
    hybrid_score = 0 if hybrid else 3.0
    # =IFS('JU NCS database'!BA="Y";0;TRUE;3)
    closed_bus_score = 0 if closed_bus else 3.0
    # =IFS('JU NCS database'!BD="Y";0;TRUE;1,5)
    hvac_heat_recovery_score = 0 if hvac_heat_recovery else 1.5
    # =IFS('JU NCS database'!BE="Y";0;TRUE;1)
    freshwater_cooling_systems_score = 0 if freshwater_cooling_systems else 1.0
    # =IFS('JU NCS database'!BF="Y";0;TRUE;2)
    seawater_cooling_systems_score = 0 if seawater_cooling_systems else 2.0
    # =IFS('JU NCS database'!BG="Y";0;TRUE;0,75)
    operator_awareness_dashboard_score = 0 if operator_awareness_dashboard else 0.75
    # =IFS('JU NCS database'!BH="Y";0;TRUE;0,5)
    hpu_optimization_score = 0 if hpu_optimization else 0.5
    # =IFS('JU NCS database'!BI="Y";0;TRUE;1)
    optimized_heat_tracing_system_score = 0 if optimized_heat_tracing_system else 1.0
    # =IFS('JU NCS database'!BJ="Y";0;TRUE;0,2)
    floodlighting_optimization_score = 0 if floodlighting_optimization else 0.2
    # =IFS('JU NCS database'!BK="Y";0;TRUE;0,5)
    vfds_on_aux_machinery_score = 0 if vfds_on_aux_machinery else 0.5
    points = sum(
        [
            vessel_size_score,
            accommodation_score,
            generator_sets_score,
            generator_set_hp_average_score,
            engine_sets_score,
            engine_set_hp_average_score,
            mudpumps_hp_total_score,
            drawworks_hp_score,
            hybrid_score,
            closed_bus_score,
            hvac_heat_recovery_score,
            freshwater_cooling_systems_score,
            seawater_cooling_systems_score,
            operator_awareness_dashboard_score,
            hpu_optimization_score,
            optimized_heat_tracing_system_score,
            floodlighting_optimization_score,
            vfds_on_aux_machinery_score,
        ]
    )
    logger.info('Calculated Jackup CO2')

    return JackupCO2Result(
        points=points,
        vessel_size=vessel_size_score,
        accommodation=accommodation_score,
        generator_sets_score=generator_sets_score,
        generator_set_hp_average=generator_set_hp_average_score,
        engine_sets_score=engine_sets_score,
        engine_set_hp_average=engine_set_hp_average_score,
        mudpumps_hp_total=mudpumps_hp_total_score,
        drawworks_hp=drawworks_hp_score,
        hybrid=hybrid_score,
        closed_bus=closed_bus_score,
        hvac_heat_recovery=hvac_heat_recovery_score,
        freshwater_cooling_systems=freshwater_cooling_systems_score,
        seawater_cooling_systems=seawater_cooling_systems_score,
        operator_awareness_dashboard=operator_awareness_dashboard_score,
        hpu_optimization=hpu_optimization_score,
        optimized_heat_tracing_system=optimized_heat_tracing_system_score,
        floodlighting_optimization=floodlighting_optimization_score,
        vfds_on_aux_machinery=vfds_on_aux_machinery_score,
    )


def calculate_reference_jackup_co2() -> JackupCO2Result:
    logger.info('Calculating Jackup CO2 for reference rig')
    return calculate_jackup_co2(
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
    )


def calculate_custom_jackup_co2(rig: CustomJackupRig) -> JackupCO2Result:
    logger.info('Calculating Jackup CO2 for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_jackup_co2(
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        quarters_capacity=rig.quarters_capacity,
        generator_qty_1=rig.generator_quantity,
        engine_qty_1=rig.engine_quantity,
        mud_total_hp=rig.mud_total_power,
        drawworks_hp=rig.drawworks_power,
        hybrid=rig.hybrid,
        closed_bus=rig.closed_bus,
        generator_kw_1=rig.generator_power,
        engine_hp_1=rig.engine_power,
        hvac_heat_recovery=rig.hvac_heat_recovery,
        freshwater_cooling_systems=rig.freshwater_cooling_systems,
        seawater_cooling_systems=rig.seawater_cooling_systems,
        operator_awareness_dashboard=rig.operator_awareness_dashboard,
        hpu_optimization=rig.hpu_optimization,
        optimized_heat_tracing_system=rig.optimized_heat_tracing_system,
        floodlighting_optimization=rig.floodlighting_optimization,
        vfds_on_aux_machinery=rig.vfds_on_aux_machinery,
    )


def calculate_custom_jackup_co2_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup CO2 score for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_custom_jackup_co2(rig)['points'] / calculate_reference_jackup_co2()['points']


class JackupMoveAndInstallationResult(TypedDict):
    points: float
    rig_management: float
    enhanced_legs: float
    leg_spacing: float


def calculate_jackup_move_and_installation(
    *,
    # 'JU NCS database'!AV
    enhanced_legs: bool,
    # 'JU NCS database'!AC
    leg_spacing_1_ft: float,
) -> JackupMoveAndInstallationResult:
    logger.info('Calculating Jackup move and installation')
    rig_management_score = 5.0
    # =IFS(
    #     'JU NCS database'!AV="Y";1;
    #     'JU NCS database'!AV="N";0;
    #     TRUE;0
    # )
    enhanced_legs_score = 1.0 if enhanced_legs else 0.0
    # ='JU NCS database'!AC/200
    leg_spacing_score = leg_spacing_1_ft / 200.0
    points = sum(
        [
            rig_management_score,
            enhanced_legs_score,
            leg_spacing_score,
        ]
    )
    logger.info('Calculated Jackup move and installation')
    return JackupMoveAndInstallationResult(
        points=points,
        rig_management=rig_management_score,
        enhanced_legs=enhanced_legs_score,
        leg_spacing=leg_spacing_score,
    )


def calculate_reference_jackup_move_and_installation() -> JackupMoveAndInstallationResult:
    logger.info('Calculating Jackup move and installation for reference rig')
    return calculate_jackup_move_and_installation(enhanced_legs=False, leg_spacing_1_ft=229.0000)


def calculate_custom_jackup_move_and_installation(rig: CustomJackupRig) -> JackupMoveAndInstallationResult:
    logger.info('Calculating Jackup move and installation for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_jackup_move_and_installation(enhanced_legs=rig.enhanced_legs, leg_spacing_1_ft=rig.leg_spacing)


def calculate_custom_jackup_move_and_installation_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup move and installation score for CustomJackupRig(pk=%s)', rig.pk)
    return (
        calculate_custom_jackup_move_and_installation(rig)['points']
        / calculate_reference_jackup_move_and_installation()['points']
    )


class JackupTopsideEfficiencyResult(TypedDict):
    points: float
    design_score: float
    topside_design: float
    derrick_height_ft: float
    mudpump_qty: float
    liquid_mud_bbl: float
    mud_total_hp: float
    offline_stand_building: float
    auto_pipe_handling: float
    dual_activity: float
    drilltronic: float
    dynamic_drilling_guide: float
    process_automation_platform: float
    automatic_tripping: float


# =IFS(
#     'JU NCS database'!L="High";2;
#     'JU NCS database'!L="Medium";1;
#     'JU NCS database'!L="Low";0;
#     TRUE;0
# )
DESIGN_SCORE_SCORE = {
    HighMediumLow.HIGH: 2,
    HighMediumLow.MEDIUM: 1,
    HighMediumLow.LOW: 0,
}


# =IFS(
#     'JU NCS database'!M="NOV";1,03;
#     'JU NCS database'!M="MH";1,02;
#     'JU NCS database'!M="Cameron";1,01;
#     TRUE;1
# )

TOPSIDE_EFFICIENCY_TOPSIDE_DESIGN_SCORE = {
    TopsideDesign.NOV: 1.03,
    TopsideDesign.MH: 1.02,
    TopsideDesign.CAMERON: 1.01,
    TopsideDesign.OTHER: 1,
}


def calculate_jackup_topside_efficiency(
    *,
    # 'JU NCS database'!L
    design_score: HighMediumLow,
    # 'JU NCS database'!M
    topside_design: TopsideDesign,
    # 'JU NCS database'!T
    derrick_height_ft: float,
    # 'JU NCS database'!AH
    mudpump_qty: float,
    # 'JU NCS database'!AI
    liquid_mud_bbl: float,
    # 'JU NCS database'!AJ
    mud_total_hp: float,
    # 'JU NCS database'!AR
    offline_stand_building: bool,
    # 'JU NCS database'!AS
    auto_pipe_handling: bool,
    # 'JU NCS database'!AT
    dual_activity: bool,
    # 'JU NCS database'!AW
    drilltronic: bool,
    # 'JU NCS database'!AX
    dynamic_drilling_guide: bool,
    # 'JU NCS database'!AY
    process_automation_platform: bool,
    # 'JU NCS database'!AZ
    automatic_tripping: bool,
) -> JackupTopsideEfficiencyResult:
    logger.info('Calculating Jackup topside efficiency')
    design_score_score = DESIGN_SCORE_SCORE[design_score]
    topside_design_score = TOPSIDE_EFFICIENCY_TOPSIDE_DESIGN_SCORE[topside_design]
    # ='JU NCS database'!T/85
    derrick_height_ft_score = derrick_height_ft / 85.0
    # ='JU NCS database'!AH*1,02
    mudpump_qty_score = mudpump_qty * 1.02
    # ='JU NCS database'!AI/989
    liquid_mud_bbl_score = liquid_mud_bbl / 989.0
    # ='JU NCS database'!AJ/8800
    mud_total_hp_score = mud_total_hp / 8800.0
    # =IFS(
    #     'JU NCS database'!AR="Y";1,98;
    #     'JU NCS database'!AR="N";0;
    #     TRUE;0
    # )
    offline_stand_building_score = 1.98 if offline_stand_building else 0
    # =IFS(
    #     'JU NCS database'!AS="Y";1,91;
    #     'JU NCS database'!AS="N";0;
    #     TRUE;0
    # )
    auto_pipe_handling_score = 1.91 if auto_pipe_handling else 0
    # =IFS(
    #     'JU NCS database'!AT="Y";1,55;
    #     'JU NCS database'!AT="N";0;
    #     TRUE;0
    # )
    dual_activity_score = 1.55 if dual_activity else 0
    # =IFS(
    #     'JU NCS database'!AW="Y";1;
    #     'JU NCS database'!AW="N";0;
    #     TRUE;0
    # )
    drilltronic_score = 1 if drilltronic else 0
    # =IFS(
    #     'JU NCS database'!AX="Y";1,07;
    #     'JU NCS database'!AX="N";0;
    #     TRUE;0
    # )
    dynamic_drilling_guide_score = 1.07 if dynamic_drilling_guide else 0
    # =IFS(
    #     'JU NCS database'!AY="Y";1,02;
    #     'JU NCS database'!AY="N";0;
    #     TRUE;0
    # )
    process_automation_platform_score = 1.02 if process_automation_platform else 0
    # =IFS(
    #     'JU NCS database'!AZ="Y";1;
    #     'JU NCS database'!AZ="N";0;
    #     TRUE;0
    # )
    automatic_tripping_score = 1 if automatic_tripping else 0
    points = sum(
        [
            design_score_score,
            topside_design_score,
            derrick_height_ft_score,
            mudpump_qty_score,
            liquid_mud_bbl_score,
            mud_total_hp_score,
            offline_stand_building_score,
            auto_pipe_handling_score,
            dual_activity_score,
            drilltronic_score,
            dynamic_drilling_guide_score,
            process_automation_platform_score,
            automatic_tripping_score,
        ]
    )
    logger.info('Calculated Jackup topside efficiency')
    return JackupTopsideEfficiencyResult(
        points=points,
        design_score=design_score_score,
        topside_design=topside_design_score,
        derrick_height_ft=derrick_height_ft_score,
        mudpump_qty=mudpump_qty_score,
        liquid_mud_bbl=liquid_mud_bbl_score,
        mud_total_hp=mud_total_hp_score,
        offline_stand_building=offline_stand_building_score,
        auto_pipe_handling=auto_pipe_handling_score,
        dual_activity=dual_activity_score,
        drilltronic=drilltronic_score,
        dynamic_drilling_guide=dynamic_drilling_guide_score,
        process_automation_platform=process_automation_platform_score,
        automatic_tripping=automatic_tripping_score,
    )


def calculate_reference_jackup_topside_efficiency() -> JackupTopsideEfficiencyResult:
    logger.info('Calculating Jackup topside efficiency for reference rig')
    return calculate_jackup_topside_efficiency(
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
    )


def calculate_custom_jackup_topside_efficiency(rig: CustomJackupRig) -> JackupTopsideEfficiencyResult:
    logger.info('Calculating Jackup topside efficiency for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_jackup_topside_efficiency(
        design_score=rig.design_score,
        topside_design=rig.topside_design,
        derrick_height_ft=rig.derrick_height,
        mudpump_qty=rig.mudpump_quantity,
        liquid_mud_bbl=rig.liquid_mud,
        mud_total_hp=rig.mud_total_power,
        offline_stand_building=rig.offline_stand_building,
        auto_pipe_handling=rig.auto_pipe_handling,
        dual_activity=rig.dual_activity,
        drilltronic=rig.drilltronic,
        dynamic_drilling_guide=rig.dynamic_drilling_guide,
        process_automation_platform=rig.process_automation_platform,
        automatic_tripping=rig.automatic_tripping,
    )


def calculate_custom_jackup_topside_efficiency_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup topside efficiency score for CustomJackupRig(pk=%s)', rig.pk)
    return (
        calculate_custom_jackup_topside_efficiency(rig)['points']
        / calculate_reference_jackup_topside_efficiency()['points']
    )


class JackupDeckEfficiencyResult(TypedDict):
    points: float
    topside_design: float
    variable_load_t: float
    cantilever_reach_ft: float
    cantilever_lateral_ft: float
    total_cranes: float
    crane_capacity: float
    vessel_size: float
    auto_pipe_handling: float


# =IFS(
#     'JU NCS database'!M="NOV";1,05;
#     'JU NCS database'!M="MH";1,04;
#     'JU NCS database'!M="Cameron";1,04;
#     'JU NCS database'!M="Other";1;
#     TRUE;0
# )
DECK_EFFICIENCY_TOPSIDE_DESIGN_SCORE = {
    TopsideDesign.NOV: 1.05,
    TopsideDesign.MH: 1.04,
    TopsideDesign.CAMERON: 1.04,
    TopsideDesign.OTHER: 1.0,
}


def calculate_jackup_deck_efficiency(
    *,
    # 'JU NCS database'!M
    topside_design: TopsideDesign,
    # 'JU NCS database'!P
    variable_load_t: float,
    # 'JU NCS database'!Q
    cantilever_reach_ft: float,
    # 'JU NCS database'!R
    cantilever_lateral_ft: float,
    # 'JU NCS database'!W
    total_cranes: float,
    # 'JU NCS database'!X
    crane_capacity: float,
    # 'JU NCS database'!Y
    hull_breadth_ft: float,
    # 'JU NCS database'!Z
    hull_depth_ft: float,
    # 'JU NCS database'!AA
    hull_length_ft: float,
    #  'JU NCS database'!AS
    auto_pipe_handling: bool,
) -> JackupDeckEfficiencyResult:
    logger.info('Calculating Jackup deck efficiency')
    topside_design_score = DECK_EFFICIENCY_TOPSIDE_DESIGN_SCORE[topside_design]
    # ='JU NCS database'!P/2000
    variable_load_t_score = variable_load_t / 2000.0
    # ='JU NCS database'!Q/9,5
    cantilever_reach_ft_score = cantilever_reach_ft / 9.5
    # ='JU NCS database'!R/5,1
    cantilever_lateral_ft_score = cantilever_lateral_ft / 5.1
    # ='JU NCS database'!W/1,1
    total_cranes_score = total_cranes / 1.1
    # ='JU NCS database'!X/52
    crane_capacity_score = crane_capacity / 52.0
    # ='JU NCS database'!Y*'JU NCS database'!Z*'JU NCS database'!AA/1000000
    vessel_size_score = hull_breadth_ft * hull_depth_ft * hull_length_ft / 1000000.0
    # =IFS(
    #     'JU NCS database'!AS="Y";2;
    #     'JU NCS database'!AS="N";0;
    #     TRUE;0
    # )
    auto_pipe_handling_score = 2 if auto_pipe_handling else 0
    points = sum(
        [
            topside_design_score,
            variable_load_t_score,
            cantilever_reach_ft_score,
            cantilever_lateral_ft_score,
            total_cranes_score,
            crane_capacity_score,
            vessel_size_score,
            auto_pipe_handling_score,
        ]
    )
    logger.info('Calculated Jackup deck efficiency')

    return JackupDeckEfficiencyResult(
        points=points,
        topside_design=topside_design_score,
        variable_load_t=variable_load_t_score,
        cantilever_reach_ft=cantilever_reach_ft_score,
        cantilever_lateral_ft=cantilever_lateral_ft_score,
        total_cranes=total_cranes_score,
        crane_capacity=crane_capacity_score,
        vessel_size=vessel_size_score,
        auto_pipe_handling=auto_pipe_handling_score,
    )


def calculate_reference_jackup_deck_efficiency() -> JackupDeckEfficiencyResult:
    logger.info('Calculating Jackup deck efficiency for reference rig')
    return calculate_jackup_deck_efficiency(
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
    )


def calculate_custom_jackup_deck_efficiency(rig: CustomJackupRig) -> JackupDeckEfficiencyResult:
    logger.info('Calculating Jackup deck efficiency for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_jackup_deck_efficiency(
        topside_design=rig.topside_design,
        variable_load_t=rig.variable_load,
        cantilever_reach_ft=rig.cantilever_reach,
        cantilever_lateral_ft=rig.cantilever_lateral,
        total_cranes=rig.total_cranes,
        crane_capacity=rig.crane_capacity,
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        auto_pipe_handling=rig.auto_pipe_handling,
    )


def calculate_custom_jackup_deck_efficiency_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup deck efficiency score for CustomJackupRig(pk=%s)', rig.pk)
    return (
        calculate_custom_jackup_deck_efficiency(rig)['points'] / calculate_reference_jackup_deck_efficiency()['points']
    )


class JackupCapacitiesResult(TypedDict):
    points: float
    quarters_capacity: float
    rig_water_depth_ft: float
    variable_load_t: float
    cantilever_reach_ft: float
    cantilever_lateral_ft: float
    cantilever_capacity_lbs: float
    derrick_height_ft: float
    total_bop_rams: float
    bop_diameter_wp_max_in: float
    mudpump_qty: float
    liquid_mud_bbl: float
    subsea_drilling: float
    enhanced_legs: float
    closed_bus: float
    hybrid: float


def calculate_jackup_capacities(
    *,
    # 'JU NCS database'!N
    quarters_capacity: float,
    # 'JU NCS database'!O
    rig_water_depth_ft: float,
    # 'JU NCS database'!P
    variable_load_t: float,
    # 'JU NCS database'!Q
    cantilever_reach_ft: float,
    # 'JU NCS database'!R
    cantilever_lateral_ft: float,
    # 'JU NCS database'!S
    cantilever_capacity_lbs: float,
    # 'JU NCS database'!T
    derrick_height_ft: float,
    # 'JU NCS database'!AD
    total_bop_rams: float,
    # 'JU NCS database'!AE
    bop_diameter_wp_max_in: float,
    # 'JU NCS database'!AH
    mudpump_qty: float,
    # 'JU NCS database'!AI
    liquid_mud_bbl: float,
    # 'JU NCS database'!AU
    subsea_drilling: bool,
    # 'JU NCS database'!AV
    enhanced_legs: bool,
    # 'JU NCS database'!BA
    closed_bus: bool,
    # 'JU NCS database'!BC
    hybrid: bool,
) -> JackupCapacitiesResult:
    logger.info('Calculating Jackup capacities')
    # ='JU NCS database'!N/100
    quarters_capacity_score = quarters_capacity / 100.0
    # ='JU NCS database'!O/250
    rig_water_depth_ft_score = rig_water_depth_ft / 250.0
    # ='JU NCS database'!P/5000
    variable_load_t_score = variable_load_t / 5000.0
    # ='JU NCS database'!Q/50
    cantilever_reach_ft_score = cantilever_reach_ft / 50.0
    # ='JU NCS database'!R/20
    cantilever_lateral_ft_score = cantilever_lateral_ft / 20
    # ='JU NCS database'!S/1000000
    cantilever_capacity_lbs_score = cantilever_capacity_lbs / 1000000.0
    # ='JU NCS database'!T/200
    derrick_height_ft_score = derrick_height_ft / 200.0
    # ='JU NCS database'!AD/0,95
    total_bop_rams_score = total_bop_rams / 0.95
    # ='JU NCS database'!AE/10
    bop_diameter_wp_max_in_score = bop_diameter_wp_max_in / 10.0
    # ='JU NCS database'!AH*0,95
    mudpump_qty_score = mudpump_qty * 0.95
    # ='JU NCS database'!AI/2000
    liquid_mud_bbl_score = liquid_mud_bbl / 2000.0
    # =IFS(
    #     'JU NCS database'!AU="Y";1;
    #     'JU NCS database'!AU="N";0;
    #     TRUE;0
    # )
    subsea_drilling_score = 1 if subsea_drilling else 0
    # =IFS(
    #     'JU NCS database'!AV="Y";1;
    #     'JU NCS database'!AV="N";0;
    #     TRUE;0
    # )
    enhanced_legs_score = 1 if enhanced_legs else 0
    # =IFS(
    #     'JU NCS database'!BA="Y";1;
    #     'JU NCS database'!BA="N";0;
    #     TRUE;0
    # )
    closed_bus_score = 1 if closed_bus else 0
    # =IFS(
    #     'JU NCS database'!BC="Y";3;
    #     'JU NCS database'!BC="N";0;
    #     TRUE;0
    # )
    hybrid_score = 3 if hybrid else 0
    points = sum(
        [
            quarters_capacity_score,
            rig_water_depth_ft_score,
            variable_load_t_score,
            cantilever_reach_ft_score,
            cantilever_lateral_ft_score,
            cantilever_capacity_lbs_score,
            derrick_height_ft_score,
            total_bop_rams_score,
            bop_diameter_wp_max_in_score,
            mudpump_qty_score,
            liquid_mud_bbl_score,
            subsea_drilling_score,
            enhanced_legs_score,
            closed_bus_score,
            hybrid_score,
        ]
    )
    logger.info('Calculated Jackup capacities')
    return JackupCapacitiesResult(
        points=points,
        quarters_capacity=quarters_capacity_score,
        rig_water_depth_ft=rig_water_depth_ft_score,
        variable_load_t=variable_load_t_score,
        cantilever_reach_ft=cantilever_reach_ft_score,
        cantilever_lateral_ft=cantilever_lateral_ft_score,
        cantilever_capacity_lbs=cantilever_capacity_lbs_score,
        derrick_height_ft=derrick_height_ft_score,
        total_bop_rams=total_bop_rams_score,
        bop_diameter_wp_max_in=bop_diameter_wp_max_in_score,
        mudpump_qty=mudpump_qty_score,
        liquid_mud_bbl=liquid_mud_bbl_score,
        subsea_drilling=subsea_drilling_score,
        enhanced_legs=enhanced_legs_score,
        closed_bus=closed_bus_score,
        hybrid=hybrid_score,
    )


def calculate_reference_jackup_capacities() -> JackupCapacitiesResult:
    logger.info('Calculating Jackup capacities for reference rig')
    return calculate_jackup_capacities(
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
    )


def calculate_custom_jackup_capacities(rig: CustomJackupRig) -> JackupCapacitiesResult:
    logger.info('Calculating Jackup capacities for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_jackup_capacities(
        quarters_capacity=rig.quarters_capacity,
        rig_water_depth_ft=rig.rig_water_depth,
        variable_load_t=rig.variable_load,
        cantilever_reach_ft=rig.cantilever_reach,
        cantilever_lateral_ft=rig.cantilever_lateral,
        cantilever_capacity_lbs=rig.cantilever_capacity,
        derrick_height_ft=rig.derrick_height,
        total_bop_rams=rig.total_bop_rams,
        bop_diameter_wp_max_in=rig.bop_diameter_wp_max,
        mudpump_qty=rig.mudpump_quantity,
        liquid_mud_bbl=rig.liquid_mud,
        subsea_drilling=rig.subsea_drilling,
        enhanced_legs=rig.enhanced_legs,
        closed_bus=rig.closed_bus,
        hybrid=rig.hybrid,
    )


def calculate_custom_jackup_capacities_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup capacities score for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_custom_jackup_capacities(rig)['points'] / calculate_reference_jackup_capacities()['points']


class JackupMoveResult(TypedDict):
    fuel_td: float
    move_time_d: float
    tug_to_field_and_return_time_d: float
    total_move_time_d: float
    total_fuel_t: float


def calculate_jackup_move(
    *,
    # 'JU CO2'!C
    co2_score: float,
    # D
    number_of_tugs: int,
    # E
    tug_boat_move_fuel_consumption_td: float,
    # F
    move_distance_nm: float,
    # G
    move_speed_kn: float,
    # I
    positioning_time_d: float,
    # J
    tug_boat_transit_to_rig_distance_nm: float,
    # K
    tug_boat_return_distance_nm: float,
    # L
    tug_boat_transit_speed_kn: float,
    # M
    tug_boat_transit_fuel_consumption_td: float,
    # O
    jack_up_time_d: float,
    # P
    jack_down_time_d: float,
) -> JackupMoveResult:
    logger.info('Calculating Jackup move')
    # C
    fuel_td = 5 * co2_score
    # H=(F/G)/24
    move_time_d = move_distance_nm / move_speed_kn / 24
    # N = (J+K)/L/24
    tug_to_field_and_return_time_d = (
        (tug_boat_transit_to_rig_distance_nm + tug_boat_return_distance_nm) / tug_boat_transit_speed_kn / 24
    )
    # Q = H+I+P+O
    total_move_time_d = move_time_d + positioning_time_d + jack_down_time_d + jack_up_time_d
    # R = C*Q+E*D*(I+H)+N*D*M
    total_fuel_t = (
        fuel_td * total_move_time_d
        + tug_boat_move_fuel_consumption_td * number_of_tugs * (positioning_time_d + move_time_d)
        + tug_to_field_and_return_time_d * number_of_tugs * tug_boat_transit_fuel_consumption_td
    )
    logger.info('Calculated Jackup move')
    return JackupMoveResult(
        fuel_td=fuel_td,
        move_time_d=move_time_d,
        tug_to_field_and_return_time_d=tug_to_field_and_return_time_d,
        total_move_time_d=total_move_time_d,
        total_fuel_t=total_fuel_t,
    )


def calculate_custom_jackup_move(*, rig: CustomJackupRig, plan: Plan, well_index: int) -> JackupMoveResult:
    logger.info(
        'Calculating Jackup move for CustomJackupRig(pk=%s), Plan(pk=%s) and well nr %s', rig.pk, plan.pk, well_index
    )
    project = plan.project
    co2_score = calculate_custom_jackup_co2_score(rig)
    plan_wells = list(PlanWellRelation.objects.filter(plan=plan).order_by('order'))
    current_plan_well = plan_wells[well_index]
    if well_index == 0:
        tug_boat_transit_to_rig_distance_nm = plan.distance_from_tug_base_to_previous_well
    else:
        tug_boat_transit_to_rig_distance_nm = plan_wells[well_index - 1].distance_to_tug_base
    return calculate_jackup_move(
        co2_score=co2_score,
        number_of_tugs=rig.tugs_no_used,
        tug_boat_move_fuel_consumption_td=project.tugs_avg_move_fuel_consumption,
        tug_boat_transit_fuel_consumption_td=project.tugs_avg_transit_fuel_consumption,
        tug_boat_transit_to_rig_distance_nm=tug_boat_transit_to_rig_distance_nm,
        tug_boat_return_distance_nm=current_plan_well.distance_to_tug_base,
        tug_boat_transit_speed_kn=project.tugs_transit_speed,
        move_distance_nm=current_plan_well.distance_from_previous_location,
        move_speed_kn=project.tugs_move_speed,
        positioning_time_d=current_plan_well.jackup_positioning_time,
        jack_up_time_d=rig.jack_up_time,
        jack_down_time_d=rig.jack_down_time,
    )


def calculate_reference_jackup_rig_status() -> RigStatusResult:
    logger.info('Calculating Jackup rig status for reference rig')
    return calculate_rig_status(
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=1, month=4, year=2013),
    )


def calculate_custom_jackup_rig_status_score(rig: CustomJackupRig) -> float:
    logger.info('Calculating Jackup rig status score for CustomJackupRig(pk=%s)', rig.pk)
    return calculate_custom_rig_status(rig)['points'] / calculate_reference_jackup_rig_status()['points']


class JackupCO2PerWellResult(TypedDict):
    fuel: float
    co2_td: float
    fuel_winter: float
    co2_winter_td: float
    fuel_summer: float
    co2_summer_td: float
    operational_days: float
    move_time: float
    total_days: float
    rig_day_rate_usd_d: float
    spread_cost: float
    fuel_per_day: float
    co2: float
    psv_trips: float
    psv_fuel: float
    psv_co2: float
    psv_cost_usd: float
    helicopter_trips: float
    helicopter_fuel: float
    helicopter_co2: float
    helicopter_cost_usd: float
    move_fuel: float
    tugs: float
    tugs_cost: float
    total_fuel: float
    total_co2: float
    total_cost: float


def calculate_jackup_co2_per_well(
    # JU CO2 pr well
    *,
    # F='JU Deck Efficiency'!C
    deck_efficiency: float,
    # M='JU CO2'!D
    co2_efficiency: float,
    # 'Comparison input'!$A$40
    fuel_density_tm3: float,
    # 'Comparison input'!$A$42
    co2_emission_per_tonne_fuel: float,
    # X
    operational_days: float,
    # Y='JU Move'!Q
    move_time: float,
    # PSV!$B$4
    psv_visits_per_7_days: float,
    # PSV!$B$19
    psv_fuel_per_trip: float,
    # PSV!$B$7
    psv_time_per_trip_d: float,
    # 'Comparison input'!A50, PSV!$B$12
    psv_day_rate: float,
    # PSV!$B$11
    psv_fuel_cost_usd_t: float,
    # Helicopter!$B$2
    helicopter_trips_per_7_days: float,
    # Helicopter!C
    helicopter_factor: float,
    # Helicopter!$B$13
    helicopter_fuel_consumption_per_trip_t: float,
    # Helicopter!$B$7
    helicopter_fuel_cost_usd_t: float,
    # Helicopter!$B$8
    helicopter_charter_price_usd: float,
    # AN='JU Move'!R
    move_fuel: float,
    # 'Comparison input'!$A$46
    tugs_day_rate: float,
    # 'Comparison input'!$A$38
    total_fuel_price: float,
    # AB
    rig_day_rate_usd_d: float,
    # AC
    rig_spread_cost: float,
    # AO='JU Move'!D
    number_of_tugs: int,
    # 'Comparison input'!$A$56
    helicopter_co2_emission_per_tonne_fuel: float,
) -> JackupCO2PerWellResult:
    logger.info('Calculating Jackup CO2 per well')
    # N=21,3/0,92*'Comparison input'!$A$40
    benchmark_td_2020_status = 21.3 / 0.92 * fuel_density_tm3
    # O,AD='JU CO2'!D*$N$2
    fuel_per_day = co2_efficiency * benchmark_td_2020_status
    # P=O*'Comparison input'!$A$42
    co2_td = fuel_per_day * co2_emission_per_tonne_fuel
    # R=O*1,03
    fuel_winter = fuel_per_day * 1.03
    # S=R*'Comparison input'!$A$42
    co2_winter_td = fuel_winter * co2_emission_per_tonne_fuel
    # U=O*0,97
    fuel_summer = fuel_per_day * 0.97
    # V=U*'Comparison input'!$A$42
    co2_summer_td = fuel_summer * co2_emission_per_tonne_fuel
    # Z=X+Y
    total_days = operational_days + move_time
    # AE=AD*'Comparison input'!$A$42
    fuel_co2 = fuel_per_day * co2_emission_per_tonne_fuel
    # AF=PSV!$B$4*(Z/7)+(1-F)*Z*0,1
    psv_trips = psv_visits_per_7_days * (total_days / 7) + (1.0 - deck_efficiency) * total_days * 0.1
    # AG=AF*PSV!$B$19
    psv_fuel = psv_trips * psv_fuel_per_trip
    # AH=AG*'Comparison input'!$A$42
    psv_co2 = psv_fuel * co2_emission_per_tonne_fuel
    # AI=AF*PSV!$B$7*PSV!$B$12+AG*PSV!$B$11
    psv_cost_usd = psv_trips * psv_time_per_trip_d * psv_day_rate + psv_fuel * psv_fuel_cost_usd_t
    # AJ=(Z*Helicopter!$B$2)/7*Helicopter!C3
    helicopter_trips = (total_days * helicopter_trips_per_7_days) / 7 * helicopter_factor
    # AK=Helicopter!$B$13*AJ
    helicopter_fuel = helicopter_fuel_consumption_per_trip_t * helicopter_trips
    # AL=AK*'Comparison input'!$A$56
    helicopter_co2 = helicopter_fuel * helicopter_co2_emission_per_tonne_fuel
    # AM=AK*Helicopter!$B$7+AJ*Helicopter!$B$8
    helicopter_cost_usd = helicopter_fuel * helicopter_fuel_cost_usd_t + helicopter_trips * helicopter_charter_price_usd
    # AP='Comparison input'!$A$46*AO
    tugs_cost = tugs_day_rate * number_of_tugs
    # AN * 'Comparison input'!$A$42
    move_co2 = move_fuel * co2_emission_per_tonne_fuel
    # AQ=AN+AK+AG+(AD*X)
    total_fuel = move_fuel + helicopter_fuel + psv_fuel + (fuel_per_day * operational_days)
    # AR=AN * 'Comparison input'!$A$42 + AL + AH + (AE * X)
    total_co2 = move_co2 + helicopter_co2 + psv_co2 + (fuel_co2 * operational_days)
    # AS=(X+Y)*(AB+AC)+AI+AM+AP+(AN+(AD*X))*'Comparison input'!$A$38
    total_cost = (
        (operational_days + move_time) * (rig_day_rate_usd_d + rig_spread_cost)
        + psv_cost_usd
        + helicopter_cost_usd
        + tugs_cost
        + (move_fuel + (fuel_per_day * operational_days)) * total_fuel_price
    )
    logger.info('Calculated Jackup CO2 per well')
    return JackupCO2PerWellResult(
        fuel=fuel_per_day,
        co2_td=co2_td,
        fuel_winter=fuel_winter,
        co2_winter_td=co2_winter_td,
        fuel_summer=fuel_summer,
        co2_summer_td=co2_summer_td,
        operational_days=operational_days,
        move_time=move_time,
        total_days=total_days,
        rig_day_rate_usd_d=rig_day_rate_usd_d,
        spread_cost=rig_spread_cost,
        fuel_per_day=fuel_per_day,
        co2=fuel_co2,
        psv_trips=psv_trips,
        psv_fuel=psv_fuel,
        psv_co2=psv_co2,
        psv_cost_usd=psv_cost_usd,
        helicopter_trips=helicopter_trips,
        helicopter_fuel=helicopter_fuel,
        helicopter_co2=helicopter_co2,
        helicopter_cost_usd=helicopter_cost_usd,
        move_fuel=move_fuel,
        tugs=number_of_tugs,
        tugs_cost=tugs_cost,
        total_fuel=total_fuel,
        total_co2=total_co2,
        total_cost=total_cost,
    )


def calculate_jackup_well_operational_days(
    # JU CO2 pr well
    *,
    # K
    efficiency: float,
    # $X$1,'Comparison input'!A4
    reference_operational_days: float,
) -> float:
    # AA=(1-K)/2
    ju_efficiency_factor = (1 - efficiency) / 2
    # X=$X$1*(1+AA)
    operational_days = reference_operational_days * (1 + ju_efficiency_factor)
    return operational_days


def calculate_jackup_well_reference_operational_days(
    # JU CO2 pr well
    *,
    # K
    efficiency: float,
    # X
    operational_days: float,
) -> float:
    # AA=(1-K)/2
    ju_efficiency_factor = (1 - efficiency) / 2
    # $X$1,'Comparison input'!A4
    reference_operational_days = operational_days / (1 + ju_efficiency_factor)
    return reference_operational_days


def calculate_custom_jackup_well_operational_days(
    *, plan: Plan, rig: CustomJackupRig, plan_well: PlanWellRelation
) -> float:
    logger.info(
        'Calculating operational days for Plan(pk=%s), CustomJackupRig(pk=%s) and PlanWellRelation(pk=%s)',
        plan.pk,
        rig.pk,
        plan_well.pk,
    )
    if plan.reference_operation_jackup == rig:
        operational_days = plan_well.operational_time
    else:
        rig_efficiency = CustomJackupSubareaScore.objects.get_or_calculate(rig).efficiency
        reference_operational_days = calculate_well_reference_operational_days(plan=plan, plan_well=plan_well)
        operational_days = calculate_jackup_well_operational_days(
            efficiency=rig_efficiency, reference_operational_days=reference_operational_days
        )
    logger.info(f'Calculated {operational_days} operational days')
    return operational_days


def calculate_custom_jackup_co2_per_well(
    *, plan: Plan, plan_well: PlanWellRelation, well_index: int, rig: CustomJackupRig
) -> JackupCO2PerWellResult:
    logger.info(
        'Calculating Jackup CO2 per well for Plan(pk=%s), PlanWellRelation(pk=%s), CustomJackupRig(pk=%s) and well nr %s',
        plan.pk,
        plan_well.pk,
        rig.pk,
        well_index,
    )
    project = plan.project
    rig_subarea_score = CustomJackupSubareaScore.objects.get_or_calculate(rig)
    operational_days = calculate_custom_jackup_well_operational_days(
        plan=plan,
        rig=rig,
        plan_well=plan_well,
    )
    move = calculate_custom_jackup_move(rig=rig, plan=plan, well_index=well_index)
    total_days = operational_days + move['total_move_time_d']
    psv = calculate_custom_psv(
        plan_well=plan_well,
        days=total_days,
    )
    helicopter = calculate_custom_helicopter(
        rig=rig,
        plan_well=plan_well,
        days=total_days,
    )

    return calculate_jackup_co2_per_well(
        deck_efficiency=rig_subarea_score.deck_efficiency,
        co2_efficiency=rig_subarea_score.co2,
        fuel_density_tm3=project.fuel_density,
        co2_emission_per_tonne_fuel=project.co2_emission_per_tonne_fuel,
        operational_days=operational_days,
        move_time=move['total_move_time_d'],
        psv_visits_per_7_days=project.psv_calls_per_week,
        psv_fuel_per_trip=psv['fuel_consumption_per_trip'],
        psv_time_per_trip_d=psv['time_per_trip_d'],
        psv_day_rate=project.psv_day_rate,
        psv_fuel_cost_usd_t=project.psv_fuel_price,
        helicopter_trips_per_7_days=project.helicopter_no_flights_per_week,
        helicopter_factor=helicopter['factor'],
        helicopter_fuel_consumption_per_trip_t=helicopter['fuel_consumption_roundtrip_t'],
        helicopter_fuel_cost_usd_t=project.helicopter_fuel_price,
        helicopter_charter_price_usd=project.helicopter_rate_per_trip,
        move_fuel=move['total_fuel_t'],
        tugs_day_rate=project.tugs_day_rate,
        total_fuel_price=project.fuel_total_price,
        rig_day_rate_usd_d=rig.day_rate or 0,
        rig_spread_cost=rig.spread_cost or 0,
        number_of_tugs=rig.tugs_no_used,
        helicopter_co2_emission_per_tonne_fuel=HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL,
    )
