import datetime
import logging
from typing import TypedDict

from apps.projects.models import Plan, PlanWellRelation, Project
from apps.rigs.models import Airgap, CustomSemiRig, CustomSemiSubareaScore, HighMediumLow, RigStatus, TopsideDesign
from apps.rigs.services.co2calculator.common import (
    HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL,
    RigStatusResult,
    calculate_custom_helicopter,
    calculate_custom_psv,
    calculate_custom_rig_status,
    calculate_rig_status,
    calculate_well_reference_operational_days,
)
from apps.wells.models import CustomWell

logger = logging.getLogger(__name__)


class SemiCO2Result(TypedDict):
    points: float
    equipment_load: float
    quarters_capacity: float
    hull_design_eco_score: float
    dp: float
    total_anchors: float
    displacement: float
    vessel_size: float
    derrick_height_ft: float
    dual_derrick: float
    drawworks_hp_hp: float
    mud_total_hp: float
    engine_horsepower_hp: float
    engine_quantity: float
    generator_effect_kw: float
    generator_qty: float
    closed_bus: float
    hybrid: float
    hvac_heat_recovery: float
    freshwater_cooling_systems: float
    seawater_cooling_systems: float
    operator_awareness_dashboard: float
    hpu_optimization: float
    optimized_heat_tracing_system: float
    floodlighting_optimization: float
    vfds_on_aux_machinery: float


# =IFS(
#     'Semi database NCS'!M="High";4;
#     'Semi database NCS'!M="Medium";2;
#     'Semi database NCS'!M="Low";1;
#     TRUE;0
# )
EQUIPMENT_LOAD_SCORE = {HighMediumLow.HIGH: 4, HighMediumLow.MEDIUM: 2, HighMediumLow.LOW: 1}

# =IFS(
#     'Semi database NCS'!X<9;4;
#     'Semi database NCS'!X<12;2;
#     TRUE;1
# )
# <9=4, 9-11=2, >=12=1


def get_total_anchors_score(total_anchors: float) -> int:
    if total_anchors < 9:
        return 4
    elif total_anchors < 12:
        return 2
    return 1


def calculate_semi_co2(
    *,
    # 'Semi database NCS'!M
    equipment_load: HighMediumLow,
    # 'Semi database NCS'!P
    quarters_capacity: float,
    # 'Semi database NCS'!T
    hull_design_eco: float,
    # 'Semi database NCS'!U
    dp: bool,
    # 'Semi database NCS'!X
    total_anchors: float,
    # 'Semi database NCS'!AB
    displacement: float,
    # 'Semi database NCS'!AC
    hull_breadth_ft: float,
    # 'Semi database NCS'!AD
    hull_depth_ft: float,
    # 'Semi database NCS'!AE
    hull_length_ft: float,
    # 'Semi database NCS'!AF
    derrick_height_ft: float,
    # 'Semi database NCS'!AH
    dual_derrick: bool,
    # 'Semi database NCS'!AI
    drawworks_hp: float,
    # 'Semi database NCS'!AU
    mudpump_total_hp: float,
    # 'Semi database NCS'!AW
    engine_hp: float,
    # 'Semi database NCS'!AY
    engine_qty_1: float,
    # 'Semi database NCS'!AZ
    generator_kw_1_kw: float,
    # 'Semi database NCS'!BA
    generator_qty_1: float,
    # 'Semi database NCS'!BK
    closed_bus: bool,
    # 'Semi database NCS'!BM=
    hybrid: bool,
    # 'Semi database NCS'!BN
    hvac_heat_recovery: bool,
    # 'Semi database NCS'!BO
    freshwater_cooling_systems: bool,
    # 'Semi database NCS'!BP
    seawater_cooling_systems: bool,
    # 'Semi database NCS'!BQ
    operator_awareness_dashboard: bool,
    # 'Semi database NCS'!BR
    hpu_optimization: bool,
    # 'Semi database NCS'!BS
    optimized_heat_tracing_system: bool,
    # 'Semi database NCS'!BT
    floodlighting_optimization: bool,
    # 'Semi database NCS'!BU
    vfds_on_aux_machinery: bool,
) -> SemiCO2Result:
    logger.info('Calculating Semi CO2')
    equipment_load_score = EQUIPMENT_LOAD_SCORE[equipment_load]
    # ='Semi database NCS'!P/35
    quarters_capacity_score = quarters_capacity / 35.0
    # =10-'Semi database NCS'!T
    hull_design_eco_score_score = 10 - hull_design_eco
    # =IFS(
    #     'Semi database NCS'!U="Y";2;
    #     'Semi database NCS'!U="N";0;
    #     TRUE;0
    # )
    dp_score = 2 if dp else 0
    total_anchors_score = get_total_anchors_score(total_anchors)
    # ='Semi database NCS'!AB/10000
    displacement_score = displacement / 10000
    # = 'Semi database NCS'!AC * 'Semi database NCS'!AD * 'Semi database NCS'!AE / 2000000
    vessel_size_score = hull_breadth_ft * hull_depth_ft * hull_length_ft / 2000000
    # ='Semi database NCS'!AF/50
    derrick_height_ft_score = derrick_height_ft / 50
    # =IFS(
    #     'Semi database NCS'!AH="Y";4;
    #     'Semi database NCS'!AH="N";2;
    #     TRUE;0
    # )
    dual_derrick_score = 4 if dual_derrick else 2
    # ='Semi database NCS'!AI/2000
    drawworks_hp_hp_score = drawworks_hp / 2000
    # ='Semi database NCS'!AU/2000
    mud_total_hp_score = mudpump_total_hp / 2000
    # ='Semi database NCS'!AW/2000
    engine_horsepower_hp_score = engine_hp / 2000
    # =(10-'Semi database NCS'!AY)/2
    engine_quantity_score = (10 - engine_qty_1) / 2
    # ='Semi database NCS'!AZ/2000
    generator_effect_kw_score = generator_kw_1_kw / 2000
    # =(10-'Semi database NCS'!BA)/2
    generator_qty_score = (10 - generator_qty_1) / 2
    # =IFS(
    #     'Semi database NCS'!BK="Y";0;
    #     'Semi database NCS'!BK="N";3;
    #     TRUE;3
    # )
    closed_bus_score = 0 if closed_bus else 3
    # =IFS(
    #     'Semi database NCS'!BM="Y";0;
    #     'Semi database NCS'!BM="N";3;
    #     TRUE;3
    # )
    hybrid_score = 0 if hybrid else 3
    # =IFS(
    #     'Semi database NCS'!BN="Y";0;
    #     'Semi database NCS'!BN="N";1,5;
    #     TRUE;1,5
    # )
    hvac_heat_recovery_score = 0 if hvac_heat_recovery else 1.5
    # =IFS(
    #     'Semi database NCS'!BO="Y";0;
    #     'Semi database NCS'!BO="N";1;
    #     TRUE;1
    # )
    freshwater_cooling_systems_score = 0 if freshwater_cooling_systems else 1
    # =IFS(
    #     'Semi database NCS'!BP="Y";0;
    #     'Semi database NCS'!BP="N";2;
    #     TRUE;2
    # )
    seawater_cooling_systems_score = 0 if seawater_cooling_systems else 2
    # =IFS(
    #     'Semi database NCS'!BQ="Y";0;
    #     'Semi database NCS'!BQ="N";0,75;
    #     TRUE;0,75
    # )
    operator_awareness_dashboard_score = 0 if operator_awareness_dashboard else 0.75
    # =IFS(
    #     'Semi database NCS'!BR="Y";0;
    #     'Semi database NCS'!BR="N";0,5;
    #     TRUE;0,5
    # )
    hpu_optimization_score = 0 if hpu_optimization else 0.5
    # =IFS(
    #     'Semi database NCS'!BS="Y";0;
    #     'Semi database NCS'!BS="N";1;
    #     TRUE;1
    # )
    optimized_heat_tracing_system_score = 0 if optimized_heat_tracing_system else 1
    # =IFS(
    #     'Semi database NCS'!BT="Y";0;
    #     'Semi database NCS'!BT="N";0,2;
    #     TRUE;0,2
    # )
    floodlighting_optimization_score = 0 if floodlighting_optimization else 0.2
    # =IFS(
    #     'Semi database NCS'!BU="Y";0;
    #     'Semi database NCS'!BU="N";0,5;
    #     TRUE;0,5
    # )
    vfds_on_aux_machinery_score = 0 if vfds_on_aux_machinery else 0.5
    points = sum(
        [
            equipment_load_score,
            quarters_capacity_score,
            hull_design_eco_score_score,
            dp_score,
            total_anchors_score,
            displacement_score,
            vessel_size_score,
            derrick_height_ft_score,
            dual_derrick_score,
            drawworks_hp_hp_score,
            mud_total_hp_score,
            engine_horsepower_hp_score,
            engine_quantity_score,
            generator_effect_kw_score,
            generator_qty_score,
            closed_bus_score,
            hybrid_score,
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
    logger.info('Calculated Semi CO2')

    return SemiCO2Result(
        points=points,
        equipment_load=equipment_load_score,
        quarters_capacity=quarters_capacity_score,
        hull_design_eco_score=hull_design_eco_score_score,
        dp=dp_score,
        total_anchors=total_anchors_score,
        displacement=displacement_score,
        vessel_size=vessel_size_score,
        derrick_height_ft=derrick_height_ft_score,
        dual_derrick=dual_derrick_score,
        drawworks_hp_hp=drawworks_hp_hp_score,
        mud_total_hp=mud_total_hp_score,
        engine_horsepower_hp=engine_horsepower_hp_score,
        engine_quantity=engine_quantity_score,
        generator_effect_kw=generator_effect_kw_score,
        generator_qty=generator_qty_score,
        closed_bus=closed_bus_score,
        hybrid=hybrid_score,
        hvac_heat_recovery=hvac_heat_recovery_score,
        freshwater_cooling_systems=freshwater_cooling_systems_score,
        seawater_cooling_systems=seawater_cooling_systems_score,
        operator_awareness_dashboard=operator_awareness_dashboard_score,
        hpu_optimization=hpu_optimization_score,
        optimized_heat_tracing_system=optimized_heat_tracing_system_score,
        floodlighting_optimization=floodlighting_optimization_score,
        vfds_on_aux_machinery=vfds_on_aux_machinery_score,
    )


def calculate_reference_semi_co2() -> SemiCO2Result:
    logger.info('Calculating Semi CO2 for reference rig')
    return calculate_semi_co2(
        equipment_load=HighMediumLow.HIGH,
        quarters_capacity=160,
        hull_design_eco=4,
        dp=True,
        total_anchors=8,
        displacement=74045.2857142857,
        hull_breadth_ft=267,
        hull_depth_ft=168.0000,
        hull_length_ft=384,
        derrick_height_ft=212,
        dual_derrick=False,
        drawworks_hp=7460,
        mudpump_total_hp=8800,
        engine_hp=7350,
        engine_qty_1=7,
        generator_kw_1_kw=5500,
        generator_qty_1=7,
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
    )


def calculate_custom_semi_co2(rig: CustomSemiRig) -> SemiCO2Result:
    logger.info('Calculating Semi CO2 for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_semi_co2(
        equipment_load=rig.equipment_load,
        quarters_capacity=rig.quarters_capacity,
        hull_design_eco=rig.hull_design_eco_score,
        dp=rig.dp,
        total_anchors=rig.total_anchors,
        displacement=rig.displacement,
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        derrick_height_ft=rig.derrick_height,
        dual_derrick=rig.dual_derrick,
        drawworks_hp=rig.drawworks_power,
        mudpump_total_hp=rig.mud_total_power,
        engine_hp=rig.engine_power,
        engine_qty_1=rig.engine_quantity,
        generator_kw_1_kw=rig.generator_power,
        generator_qty_1=rig.generator_quantity,
        closed_bus=rig.closed_bus,
        hybrid=rig.hybrid,
        hvac_heat_recovery=rig.hvac_heat_recovery,
        freshwater_cooling_systems=rig.freshwater_cooling_systems,
        seawater_cooling_systems=rig.seawater_cooling_systems,
        operator_awareness_dashboard=rig.operator_awareness_dashboard,
        hpu_optimization=rig.hpu_optimization,
        optimized_heat_tracing_system=rig.optimized_heat_tracing_system,
        floodlighting_optimization=rig.floodlighting_optimization,
        vfds_on_aux_machinery=rig.vfds_on_aux_machinery,
    )


def calculate_custom_semi_co2_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi CO2 score for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_custom_semi_co2(rig)['points'] / calculate_reference_semi_co2()['points']


class SemiTopsideEfficiencyResult(TypedDict):
    points: float
    topside_design: float
    drillfloor_efficiency: float
    dual_derrick: float
    tripsaver: float
    offline_standbuilding: float
    auto_pipe_handling: float
    dual_activity: float
    drilltronic: float
    dynamic_drilling_guide: float
    process_automation_platform: float
    automatic_tripping: float


# =IFS(
#     'Semi database NCS'!N="NOV";1,05;
#     'Semi database NCS'!N="MH";1,04;
#     'Semi database NCS'!N="Cameron";1,04;
#     TRUE;1
# )
TOPSIDE_EFFICIENCY_TOPSIDE_DESIGN_SCORE = {
    TopsideDesign.NOV: 1.05,
    TopsideDesign.MH: 1.04,
    TopsideDesign.CAMERON: 1.04,
    TopsideDesign.OTHER: 1,
}

# =IFS(
#     'Semi database NCS'!O="High";5;
#     'Semi database NCS'!O="Medium";2;
#     TRUE;0
# )
DRILLFLOOR_EFFICIENCY_SCORE = {HighMediumLow.HIGH: 5, HighMediumLow.MEDIUM: 2, HighMediumLow.LOW: 0}


def calculate_semi_topside_efficiency(
    *,
    # 'Semi database NCS'!N
    topside_design: TopsideDesign,
    # 'Semi database NCS'!O
    drillfloor_efficiency: HighMediumLow,
    # 'Semi database NCS'!AH
    dual_derrick: bool,
    # 'Semi database NCS'!BC
    tripsaver: bool,
    # 'Semi database NCS'!BD
    offline_stand_building: bool,
    # 'Semi database NCS'!BE
    auto_pipe_handling: bool,
    # 'Semi database NCS'!BF
    dual_activity: bool,
    # 'Semi database NCS'!BG
    drilltronic: bool,
    # 'Semi database NCS'!BH
    dynamic_drilling_guideline: bool,
    # 'Semi database NCS'!BI
    process_automation_platform: bool,
    # 'Semi database NCS'!BJ
    automatic_tripping: bool,
) -> SemiTopsideEfficiencyResult:
    logger.info('Calculating Semi topside efficiency')
    topside_design_score = TOPSIDE_EFFICIENCY_TOPSIDE_DESIGN_SCORE[topside_design]
    drillfloor_efficiency_score = DRILLFLOOR_EFFICIENCY_SCORE[drillfloor_efficiency]
    # =IFS(
    #     'Semi database NCS'!AH="Y";3;
    #     'Semi database NCS'!AH="N";0;
    #     TRUE;0
    # )
    dual_derrick_score = 3 if dual_derrick else 0
    # =IFS(
    #     'Semi database NCS'!AH="Y";0;
    #     'Semi database NCS'!BC="Y";1;
    #     'Semi database NCS'!BC="N";0;
    #     TRUE;0
    # )
    tripsaver_score = 0 if dual_derrick else 1 if tripsaver else 0
    # =IFS(
    #     'Semi database NCS'!BD="Y";2;
    #     'Semi database NCS'!BD="N";0;
    #     TRUE;0
    # )
    offline_standbuilding_score = 2 if offline_stand_building else 0
    # =IFS(
    #     'Semi database NCS'!BE="Y";3;
    #     'Semi database NCS'!BE="N";0;
    #     TRUE;0
    # )
    auto_pipe_handling_score = 3 if auto_pipe_handling else 0
    # =IFS(
    #     'Semi database NCS'!BF="Y";2;
    #     'Semi database NCS'!BF="N";0;
    #     TRUE;0
    # )
    dual_activity_score = 2 if dual_activity else 0
    # =IFS(
    #     'Semi database NCS'!BG="Y";1;
    #     'Semi database NCS'!BG="N";0;
    #     TRUE;0
    # )
    drilltronic_score = 1 if drilltronic else 0
    # =IFS(
    #     'Semi database NCS'!BH="Y";1,5;
    #     'Semi database NCS'!BH="N";0;
    #     TRUE;0
    # )
    dynamic_drilling_guide_score = 1.5 if dynamic_drilling_guideline else 0
    # =IFS(
    #     'Semi database NCS'!BI="Y";1,5;
    #     'Semi database NCS'!BI="N";0;
    #     TRUE;0
    # )
    process_automation_platform_score = 1.5 if process_automation_platform else 0
    # =IFS(
    #     'Semi database NCS'!BJ="Y";1;
    #     'Semi database NCS'!BJ="N";0;
    #     TRUE;0
    # )
    automatic_tripping_score = 1 if automatic_tripping else 0
    points = sum(
        [
            topside_design_score,
            drillfloor_efficiency_score,
            dual_derrick_score,
            tripsaver_score,
            offline_standbuilding_score,
            auto_pipe_handling_score,
            dual_activity_score,
            drilltronic_score,
            dynamic_drilling_guide_score,
            process_automation_platform_score,
            automatic_tripping_score,
        ]
    )
    logger.info('Calculated Semi topside efficiency')
    return SemiTopsideEfficiencyResult(
        points=points,
        topside_design=topside_design_score,
        drillfloor_efficiency=drillfloor_efficiency_score,
        dual_derrick=dual_derrick_score,
        tripsaver=tripsaver_score,
        offline_standbuilding=offline_standbuilding_score,
        auto_pipe_handling=auto_pipe_handling_score,
        dual_activity=dual_activity_score,
        drilltronic=drilltronic_score,
        dynamic_drilling_guide=dynamic_drilling_guide_score,
        process_automation_platform=process_automation_platform_score,
        automatic_tripping=automatic_tripping_score,
    )


def calculate_reference_semi_topside_efficiency() -> SemiTopsideEfficiencyResult:
    logger.info('Calculating Semi topside efficiency for reference rig')
    return calculate_semi_topside_efficiency(
        topside_design=TopsideDesign.NOV,
        drillfloor_efficiency=HighMediumLow.MEDIUM,
        dual_derrick=False,
        tripsaver=True,
        offline_stand_building=True,
        auto_pipe_handling=True,
        dual_activity=True,
        drilltronic=False,
        dynamic_drilling_guideline=False,
        process_automation_platform=False,
        automatic_tripping=False,
    )


def calculate_custom_semi_topside_efficiency(rig: CustomSemiRig) -> SemiTopsideEfficiencyResult:
    logger.info('Calculating Semi topside efficiency for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_semi_topside_efficiency(
        topside_design=rig.topside_design,
        drillfloor_efficiency=rig.drillfloor_efficiency,
        dual_derrick=rig.dual_derrick,
        tripsaver=rig.tripsaver,
        offline_stand_building=rig.offline_stand_building,
        auto_pipe_handling=rig.auto_pipe_handling,
        dual_activity=rig.dual_activity,
        drilltronic=rig.drilltronic,
        dynamic_drilling_guideline=rig.dynamic_drilling_guide,
        process_automation_platform=rig.process_automation_platform,
        automatic_tripping=rig.automatic_tripping,
    )


def calculate_custom_semi_topside_efficiency_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi topside efficiency score for CustomSemiRig(pk=%s)', rig.pk)
    return (
        calculate_custom_semi_topside_efficiency(rig)['points']
        / calculate_reference_semi_topside_efficiency()['points']
    )


class SemiDeckEfficiencyResult(TypedDict):
    points: float
    topside_design: float
    variable_deckload: float
    size: float
    decksize: float
    total_cranes: float
    crane_capacity: float
    auto_pipe_handling: float


# =IFS(
#     'Semi database NCS'!N="NOV";1,05;
#     'Semi database NCS'!N="MH";1,04;
#     'Semi database NCS'!N="Cameron";1,04;
#     TRUE;1
# )
DECK_EFFICIENCY_TOPSIDE_DESIGN_SCORE = {
    TopsideDesign.NOV: 1.05,
    TopsideDesign.MH: 1.04,
    TopsideDesign.CAMERON: 1.04,
    TopsideDesign.OTHER: 1.0,
}


def get_variable_deckload_score(variable_load_tons: float) -> float:
    # =IFS(
    #     GESTEP('Semi database NCS'!R/1000; 10);10;
    #     TRUE;'Semi database NCS'!R/1000
    # )
    score = variable_load_tons / 1000
    if score > 10:
        return 10
    return score


def calculate_semi_deck_efficiency(
    *,
    # 'Semi database NCS'!N
    topside_design: TopsideDesign,
    # 'Semi database NCS'!R
    variable_load_tons: float,
    # 'Semi database NCS'!AC
    hull_breadth_ft: float,
    # 'Semi database NCS'!AD
    hull_depth_ft: float,
    # 'Semi database NCS'!AE
    hull_length_ft: float,
    # 'Semi database NCS'!AM
    total_cranes: float,
    # 'Semi database NCS'!AN
    crane_capacity_1_tons: float,
    # 'Semi database NCS'!BE
    auto_pipe_handling: float,
) -> SemiDeckEfficiencyResult:
    logger.info('Calculating Semi deck efficiency')
    topside_design_score = DECK_EFFICIENCY_TOPSIDE_DESIGN_SCORE[topside_design]
    variable_deckload_score = get_variable_deckload_score(variable_load_tons)
    # =('Semi database NCS'!AC*'Semi database NCS'!AD*'Semi database NCS'!AE)/2000000
    size_score = (hull_breadth_ft * hull_depth_ft * hull_length_ft) / 2000000
    # =('Semi database NCS'!AC*'Semi database NCS'!AE)/20000
    decksize_score = (hull_breadth_ft * hull_length_ft) / 20000
    # ='Semi database NCS'!AM / 1,1
    total_cranes_score = total_cranes / 1.1
    # ='Semi database NCS'!AN/52
    crane_capacity_score = crane_capacity_1_tons / 52
    # =IFS(
    #     'Semi database NCS'!BE="Y";3;
    #     'Semi database NCS'!BE="N";0;
    #     TRUE;0
    # )
    auto_pipe_handling_score = 3 if auto_pipe_handling else 0

    points = sum(
        [
            topside_design_score,
            variable_deckload_score,
            size_score,
            decksize_score,
            total_cranes_score,
            crane_capacity_score,
            auto_pipe_handling_score,
        ]
    )
    logger.info('Calculated Semi deck efficiency')
    return SemiDeckEfficiencyResult(
        points=points,
        topside_design=topside_design_score,
        variable_deckload=variable_deckload_score,
        size=size_score,
        decksize=decksize_score,
        total_cranes=total_cranes_score,
        crane_capacity=crane_capacity_score,
        auto_pipe_handling=auto_pipe_handling_score,
    )


def calculate_reference_semi_deck_efficiency() -> SemiDeckEfficiencyResult:
    logger.info('Calculating Semi deck efficiency for reference rig')
    return calculate_semi_deck_efficiency(
        topside_design=TopsideDesign.NOV,
        variable_load_tons=7366,
        hull_breadth_ft=267.0000,
        hull_depth_ft=168.0000,
        hull_length_ft=384.0000,
        total_cranes=2,
        crane_capacity_1_tons=108,
        auto_pipe_handling=True,
    )


def calculate_custom_semi_deck_efficiency(rig: CustomSemiRig) -> SemiDeckEfficiencyResult:
    logger.info('Calculating Semi deck efficiency for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_semi_deck_efficiency(
        topside_design=rig.topside_design,
        variable_load_tons=rig.variable_load,
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        total_cranes=rig.total_cranes,
        crane_capacity_1_tons=rig.crane_capacity,
        auto_pipe_handling=rig.auto_pipe_handling,
    )


def calculate_custom_semi_deck_efficiency_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi deck efficiency score for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_custom_semi_deck_efficiency(rig)['points'] / calculate_reference_semi_deck_efficiency()['points']


class SemiWoWResult(TypedDict):
    points: float
    hull_concept: float
    airgap: float
    displacement: float
    vessel_size: float
    active_heave_drawwork: float
    crown_mounted_compensator_with_active_heave: float
    ram_system: float
    engine_qty: float
    engines_total_hp: float
    generator_qty: float
    generator_total_hp: float
    closed_bus: float


# =IFS(
#     'Semi database NCS'!Z="XL";5;
#     'Semi database NCS'!Z="L";4;
#     'Semi database NCS'!Z="M";3;
#     'Semi database NCS'!Z="S";1;
#     TRUE;0
# )
WOW_AIRGAP_SCORE = {
    Airgap.XL: 5,
    Airgap.L: 4,
    Airgap.M: 3,
    Airgap.S: 1,
}


def calculate_semi_wow(
    *,
    # 'Semi database NCS'!S
    hull_concept: float,
    # 'Semi database NCS'!Z
    airgap: Airgap,
    # 'Semi database NCS'!AB
    displacement: float,
    # 'Semi database NCS'!AC
    hull_breadth_ft: float,
    # 'Semi database NCS'!AD
    hull_depth_ft: float,
    # 'Semi database NCS'!AE
    hull_length_ft: float,
    # 'Semi database NCS'!AJ
    active_heave_drawwork: bool,
    # 'Semi database NCS'!AK
    cmc_with_active_heave: bool,
    # 'Semi database NCS'!AL
    ram_system: bool,
    # 'Semi database NCS'!AX
    engine_total_hp: float,
    # 'Semi database NCS'!AY
    engine_qty_1: float,
    # 'Semi database NCS'!BA
    generator_qty_1: float,
    # 'Semi database NCS'!BB
    generator_total_hp: float,
    # 'Semi database NCS'!BK
    closed_bus: bool,
) -> SemiWoWResult:
    logger.info('Calculating Semi WoW')
    # ='Semi database NCS'!S
    hull_concept_score = hull_concept
    airgap_score = WOW_AIRGAP_SCORE[airgap]
    # ='Semi database NCS'!AB / 85000
    displacement_score = displacement / 85000
    # = 'Semi database NCS'!AC * 'Semi database NCS'!AD * 'Semi database NCS'!AE / 5000000
    vessel_size_score = hull_breadth_ft * hull_depth_ft * hull_length_ft / 5000000
    # =IFS(
    #     'Semi database NCS'!AJ="Y";6;
    #     'Semi database NCS'!AJ="N";0;
    #     TRUE;0
    # )
    active_heave_drawwork_score = 6 if active_heave_drawwork else 0
    # =IFS(
    #     'Semi database NCS'!AK="Y";3;
    #     'Semi database NCS'!AK="N";0;
    #     TRUE;0
    # )
    crown_mounted_compensator_with_active_heave_score = 3 if cmc_with_active_heave else 0
    # =IFS(
    #     'Semi database NCS'!AL="Y";3;
    #     'Semi database NCS'!AL="N";0;
    #     TRUE;0
    # )
    ram_system_score = 3 if ram_system else 0
    # ='Semi database NCS'!AY/4
    engine_qty_score = engine_qty_1 / 4
    # ='Semi database NCS'!AX/30000
    engines_total_hp_score = engine_total_hp / 30000
    # ='Semi database NCS'!BA/4
    generator_qty_score = generator_qty_1 / 4
    # ='Semi database NCS'!BB/30000
    generator_total_hp_score = generator_total_hp / 30000
    # =IFS(
    #     'Semi database NCS'!BK="Y";1;
    #     'Semi database NCS'!BK="N";0;
    #     TRUE;0
    # )
    closed_bus_score = 1 if closed_bus else 0

    points = sum(
        [
            hull_concept_score,
            airgap_score,
            displacement_score,
            vessel_size_score,
            active_heave_drawwork_score,
            crown_mounted_compensator_with_active_heave_score,
            ram_system_score,
            engine_qty_score,
            engines_total_hp_score,
            generator_qty_score,
            generator_total_hp_score,
            closed_bus_score,
        ]
    )
    logger.info('Calculated Semi WoW')
    return SemiWoWResult(
        points=points,
        hull_concept=hull_concept_score,
        airgap=airgap_score,
        displacement=displacement_score,
        vessel_size=vessel_size_score,
        active_heave_drawwork=active_heave_drawwork_score,
        crown_mounted_compensator_with_active_heave=crown_mounted_compensator_with_active_heave_score,
        ram_system=ram_system_score,
        engine_qty=engine_qty_score,
        engines_total_hp=engines_total_hp_score,
        generator_qty=generator_qty_score,
        generator_total_hp=generator_total_hp_score,
        closed_bus=closed_bus_score,
    )


def calculate_reference_semi_wow() -> SemiWoWResult:
    logger.info('Calculating Semi WoW for reference rig')
    return calculate_semi_wow(
        hull_concept=9.0000,
        airgap=Airgap.M,
        displacement=74045.2857142857,
        hull_breadth_ft=267.0000,
        hull_depth_ft=168.0000,
        hull_length_ft=384.0000,
        active_heave_drawwork=True,
        cmc_with_active_heave=True,
        ram_system=False,
        engine_total_hp=51450.0000,
        engine_qty_1=7,
        generator_qty_1=7,
        generator_total_hp=38500.0000,
        closed_bus=False,
    )


def calculate_custom_semi_wow(rig: CustomSemiRig) -> SemiWoWResult:
    logger.info('Calculating Semi WoW for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_semi_wow(
        hull_concept=rig.hull_concept_score,
        airgap=rig.airgap,
        displacement=rig.displacement,
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        active_heave_drawwork=rig.active_heave_drawwork,
        cmc_with_active_heave=rig.cmc_with_active_heave,
        ram_system=rig.ram_system,
        engine_total_hp=rig.engine_total,
        engine_qty_1=rig.engine_quantity,
        generator_qty_1=rig.generator_quantity,
        generator_total_hp=rig.generator_total,
        closed_bus=rig.closed_bus,
    )


def calculate_custom_semi_wow_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi WoW score for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_custom_semi_wow(rig)['points'] / calculate_reference_semi_wow()['points']


class SemiCapacitiesResult(TypedDict):
    points: float
    quarters_capacity: float
    water_depth: float
    variable_load_t: float
    size: float
    derrick_height: float
    derrick_capacity_lbs: float
    dual_derrick: float
    drawworks_hp_hp: float
    total_bop_rams: float
    bop_diameter_working_pressure_max_in: float
    bop_wp_max: float
    number_of_bop_stacks: float
    mudpump_qty: float
    liquid_mud_bbl: float
    engine_quantity: float
    engines_capacity: float
    number_of_generators: float
    generator_capacity: float
    closed_bus: float
    hybrid: float


def calculate_semi_capacities(
    *,
    # 'Semi database NCS'!P
    quarters_capacity: float,
    # 'Semi database NCS'!Q
    rig_water_depth_ft: float,
    # 'Semi database NCS'!R
    variable_load_tons: float,
    # 'Semi database NCS'!AC
    hull_breadth_ft: float,
    # 'Semi database NCS'!AD
    hull_depth_ft: float,
    # 'Semi database NCS'!AE
    hull_length_ft: float,
    # 'Semi database NCS'!AF
    derrick_height_ft: float,
    # 'Semi database NCS'!AG
    derrick_capacity_lbs: float,
    # 'Semi database NCS'!AH
    dual_derrick: bool,
    # 'Semi database NCS'!AI
    drawworks_hp: float,
    # 'Semi database NCS'!AO
    total_bop_rams: float,
    # 'Semi database NCS'!AP
    bop_diameter_wp_max_in: float,
    # 'Semi database NCS'!AQ
    bop_wp_max_psi: float,
    # 'Semi database NCS'!AR
    number_of_bop_stacks: float,
    # 'Semi database NCS'!AS
    mudpump_qty: float,
    # 'Semi database NCS'!AT
    liquid_mud_bbl: float,
    # 'Semi database NCS'!AY
    engine_qty_1: float,
    # 'Semi database NCS'!AX
    engine_total_hp: float,
    # 'Semi database NCS'!BA
    generator_qty_1: float,
    # 'Semi database NCS'!BB
    generator_total_hp: float,
    # 'Semi database NCS'!BK
    closed_bus: bool,
    # 'Semi database NCS'!BM
    hybrid: bool,
) -> SemiCapacitiesResult:
    logger.info('Calculating Semi capacities')
    # ='Semi database NCS'!P/50
    quarters_capacity_score = quarters_capacity / 50
    # ='Semi database NCS'!Q/2500
    water_depth_score = rig_water_depth_ft / 2500
    # ='Semi database NCS'!R/2500
    variable_load_t_score = variable_load_tons / 2500
    # =('Semi database NCS'!AC*'Semi database NCS'!AD*'Semi database NCS'!AE)/2000000
    size_score = (hull_breadth_ft * hull_depth_ft * hull_length_ft) / 2000000
    # ='Semi database NCS'!AF/50
    derrick_height_score = derrick_height_ft / 50
    # ='Semi database NCS'!AG/1000000
    derrick_capacity_lbs_score = derrick_capacity_lbs / 1000000
    # =IFS(
    #     'Semi database NCS'!AH="Y";2;
    #     'Semi database NCS'!AH="N";0;
    #     TRUE;0
    # )
    dual_derrick_score = 2 if dual_derrick else 0
    # ='Semi database NCS'!AI/5000
    drawworks_hp_hp_score = drawworks_hp / 5000
    # ='Semi database NCS'!AO/2
    total_bop_rams_score = total_bop_rams / 2
    # ='Semi database NCS'!AP/10
    bop_diameter_working_pressure_max_in_score = bop_diameter_wp_max_in / 10
    # ='Semi database NCS'!AQ/10000
    bop_wp_max_score = bop_wp_max_psi / 10000
    # ='Semi database NCS'!AR
    number_of_bop_stacks_score = number_of_bop_stacks
    # ='Semi database NCS'!AS*0,75
    mudpump_qty_score = mudpump_qty * 0.75
    # ='Semi database NCS'!AT/5000
    liquid_mud_bbl_score = liquid_mud_bbl / 5000
    # ='Semi database NCS'!AY/2
    engine_quantity_score = engine_qty_1 / 2
    # ='Semi database NCS'!AX/20000
    engines_capacity_score = engine_total_hp / 20000
    # ='Semi database NCS'!BA/2
    number_of_generators_score = generator_qty_1 / 2
    # ='Semi database NCS'!BB/20000
    generator_capacity_score = generator_total_hp / 20000
    # =IFS(
    #     'Semi database NCS'!BK="Y";2;
    #     'Semi database NCS'!BK="N";0;
    #     TRUE;0
    # )
    closed_bus_score = 2 if closed_bus else 0
    # =IFS(
    #     'Semi database NCS'!BM="Y";2;
    #     'Semi database NCS'!BM="N";0;
    #     TRUE;0
    # )
    hybrid_score = 2 if hybrid else 0
    points = sum(
        [
            quarters_capacity_score,
            water_depth_score,
            variable_load_t_score,
            size_score,
            derrick_height_score,
            derrick_capacity_lbs_score,
            dual_derrick_score,
            drawworks_hp_hp_score,
            total_bop_rams_score,
            bop_diameter_working_pressure_max_in_score,
            bop_wp_max_score,
            number_of_bop_stacks_score,
            mudpump_qty_score,
            liquid_mud_bbl_score,
            engine_quantity_score,
            engines_capacity_score,
            number_of_generators_score,
            generator_capacity_score,
            closed_bus_score,
            hybrid_score,
        ]
    )
    logger.info('Calculated Semi capacities')
    return SemiCapacitiesResult(
        points=points,
        quarters_capacity=quarters_capacity_score,
        water_depth=water_depth_score,
        variable_load_t=variable_load_t_score,
        size=size_score,
        derrick_height=derrick_height_score,
        derrick_capacity_lbs=derrick_capacity_lbs_score,
        dual_derrick=dual_derrick_score,
        drawworks_hp_hp=drawworks_hp_hp_score,
        total_bop_rams=total_bop_rams_score,
        bop_diameter_working_pressure_max_in=bop_diameter_working_pressure_max_in_score,
        bop_wp_max=bop_wp_max_score,
        number_of_bop_stacks=number_of_bop_stacks_score,
        mudpump_qty=mudpump_qty_score,
        liquid_mud_bbl=liquid_mud_bbl_score,
        engine_quantity=engine_quantity_score,
        engines_capacity=engines_capacity_score,
        number_of_generators=number_of_generators_score,
        generator_capacity=generator_capacity_score,
        closed_bus=closed_bus_score,
        hybrid=hybrid_score,
    )


def calculate_reference_semi_capacities() -> SemiCapacitiesResult:
    logger.info('Calculating Semi capacities for reference rig')
    return calculate_semi_capacities(
        quarters_capacity=160.0000,
        rig_water_depth_ft=10000.0000,
        variable_load_tons=7366.0000,
        hull_breadth_ft=267.0000,
        hull_depth_ft=168.0000,
        hull_length_ft=384.0000,
        derrick_height_ft=212.0000,
        derrick_capacity_lbs=2272750,
        dual_derrick=False,
        drawworks_hp=7460,
        total_bop_rams=6,
        bop_diameter_wp_max_in=18.7500,
        bop_wp_max_psi=15000,
        number_of_bop_stacks=1,
        mudpump_qty=4,
        liquid_mud_bbl=16619.0000,
        engine_qty_1=7.0000,
        engine_total_hp=51450.0000,
        generator_qty_1=7,
        generator_total_hp=38500.0000,
        closed_bus=False,
        hybrid=False,
    )


def calculate_custom_semi_capacities(rig: CustomSemiRig) -> SemiCapacitiesResult:
    logger.info('Calculating Semi capacities for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_semi_capacities(
        quarters_capacity=rig.quarters_capacity,
        rig_water_depth_ft=rig.rig_water_depth,
        variable_load_tons=rig.variable_load,
        hull_breadth_ft=rig.hull_breadth,
        hull_depth_ft=rig.hull_depth,
        hull_length_ft=rig.hull_length,
        derrick_height_ft=rig.derrick_height,
        derrick_capacity_lbs=rig.derrick_capacity,
        dual_derrick=rig.dual_derrick,
        drawworks_hp=rig.drawworks_power,
        total_bop_rams=rig.total_bop_rams,
        bop_diameter_wp_max_in=rig.bop_diameter_wp_max,
        bop_wp_max_psi=rig.bop_wp_max,
        number_of_bop_stacks=rig.number_of_bop_stacks,
        mudpump_qty=rig.mudpump_quantity,
        liquid_mud_bbl=rig.liquid_mud,
        engine_qty_1=rig.engine_quantity,
        engine_total_hp=rig.engine_total,
        generator_qty_1=rig.generator_quantity,
        generator_total_hp=rig.generator_total,
        closed_bus=rig.closed_bus,
        hybrid=rig.hybrid,
    )


def calculate_custom_semi_capacities_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi capacities score for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_custom_semi_capacities(rig)['points'] / calculate_reference_semi_capacities()['points']


def calculate_reference_semi_rig_status() -> RigStatusResult:
    logger.info('Calculating Semi rig status for reference rig')
    return calculate_rig_status(
        rig_status=RigStatus.DRILLING,
        months_in_operation_last_year=6,
        months_in_operation_last_3_years=18,
        delivery_date=datetime.date(day=4, month=7, year=2019),
    )


def calculate_custom_semi_rig_status_score(rig: CustomSemiRig) -> float:
    logger.info('Calculating Semi rig status score for CustomSemiRig(pk=%s)', rig.pk)
    return calculate_custom_rig_status(rig)['points'] / calculate_reference_semi_rig_status()['points']


class SemiTransitResult(TypedDict):
    fuel_td_transit: float
    fuel_td_positioning: float
    number_of_tugs: float
    tugs_fuel_td: float
    move_distance_nm: float
    move_speed_kn: float
    move_time_d: float
    positioning_time: float
    lack_of_dp_for_drilling_while_installing: float
    total_fuel: float
    total_move_time: float


def calculate_semi_transit(
    *,
    # 'Semi CO2'!C
    co2_score: float,
    # D, IFS('Semi database NCS'!U="Y";'Semi CO2 pr well'!O;TRUE;'Semi CO2 pr well'!V)
    fuel_td_positioning: float,
    # E
    number_of_tugs: float,
    # F
    tugs_fuel_td: float,
    # G
    move_distance_nm: float,
    # H
    move_speed_kn: float,
    # J
    positioning_time: float,
    # 'Semi database NCS'!U
    dp: bool,
) -> SemiTransitResult:
    logger.info('Calculating Semi transit')
    # C='Semi CO2'!C*100
    fuel_td_transit = co2_score * 100
    # I=(G/H)/24
    move_time_d = move_distance_nm / move_speed_kn / 24
    # K=IFS(
    #     'Semi database NCS'!U="Y";0;
    #     'Semi database NCS'!U="N";3;
    #     TRUE;3
    # )
    lack_of_dp_for_drilling_while_installing = 0 if dp else 3
    # L=C*I+J*D+K*D
    total_fuel = (
        fuel_td_transit * move_time_d
        + positioning_time * fuel_td_positioning
        + lack_of_dp_for_drilling_while_installing * fuel_td_positioning
    )
    # M=I+J+K
    total_move_time = move_time_d + positioning_time + lack_of_dp_for_drilling_while_installing
    logger.info('Calculated Semi transit')
    return SemiTransitResult(
        fuel_td_transit=fuel_td_transit,
        fuel_td_positioning=fuel_td_positioning,
        number_of_tugs=number_of_tugs,
        tugs_fuel_td=tugs_fuel_td,
        move_distance_nm=move_distance_nm,
        move_speed_kn=move_speed_kn,
        move_time_d=move_time_d,
        positioning_time=positioning_time,
        lack_of_dp_for_drilling_while_installing=lack_of_dp_for_drilling_while_installing,
        total_fuel=total_fuel,
        total_move_time=total_move_time,
    )


def calculate_custom_semi_transit(rig: CustomSemiRig, plan_well: PlanWellRelation) -> SemiTransitResult:
    logger.info('Calculating Semi transit for CustomSemiRig(pk=%s)', rig.pk)
    project = plan_well.plan.project
    rig_subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(rig)
    semi_co2_per_well = calculate_custom_semi_common_co2_per_well(rig)

    return calculate_semi_transit(
        co2_score=rig_subarea_score.co2,
        fuel_td_positioning=semi_co2_per_well['fuel'],
        number_of_tugs=0 if rig.dp else rig.tugs_no_used,
        tugs_fuel_td=0 if rig.dp else project.tugs_avg_move_fuel_consumption,
        move_distance_nm=plan_well.distance_from_previous_location,
        move_speed_kn=rig.move_speed if rig.dp else project.tugs_move_speed,
        positioning_time=plan_well.semi_positioning_time,
        dp=rig.dp,
    )


class SemiCO2PerWell(TypedDict):
    fuel: float
    co2: float
    fuel_winter: float
    fuel_summer: float


def calculate_semi_common_co2_per_well(
    *,
    # 'Semi database NCS'!U
    dp: bool,
    # M, 'Semi CO2 '!C
    co2_score: float,
    # 'Comparison input'!$A$42
    co2_emission_per_tonne_fuel: float,
) -> SemiCO2PerWell:
    if dp:
        # O=M*51.3
        fuel = co2_score * 51.3
        # P=O*'Comparison input'!$A$42
        co2 = fuel * co2_emission_per_tonne_fuel
        # R=O*1,09
        fuel_winter = fuel * 1.09
        # T=O*0,92
        fuel_summer = fuel * 0.92
        return SemiCO2PerWell(
            fuel=fuel,
            co2=co2,
            fuel_winter=fuel_winter,
            fuel_summer=fuel_summer,
        )
    else:
        # V=M*40
        fuel = co2_score * 40
        # W=V*'Comparison input'!$A$42
        co2 = fuel * co2_emission_per_tonne_fuel
        # Y=V*1.085
        fuel_winter = fuel * 1.085
        # AA=V*0,915
        fuel_summer = fuel * 0.915
        return SemiCO2PerWell(
            fuel=fuel,
            co2=co2,
            fuel_winter=fuel_winter,
            fuel_summer=fuel_summer,
        )


def calculate_custom_semi_common_co2_per_well(rig: CustomSemiRig) -> SemiCO2PerWell:
    assert rig.project is not None
    rig_subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(rig)
    return calculate_semi_common_co2_per_well(
        dp=rig.dp, co2_score=rig_subarea_score.co2, co2_emission_per_tonne_fuel=rig.project.co2_emission_per_tonne_fuel
    )


def calculate_semi_metocean_factor(
    *,
    # 'Comparison input'!$A$54
    metocean_days_above_hs_5: float,
    # 'Semi WoW'!C
    wow_score: float,
) -> float:
    logger.info('Calculating Semi Metocean factor')
    # =(('Comparison input'!$A$54)*(2-'Semi WoW'!C))/200
    factor = (metocean_days_above_hs_5 * (2 - wow_score)) / 200
    logger.info('Calculated Semi Metocean factor')
    return factor


def calculate_custom_semi_metocean_factor(rig: CustomSemiRig, well: CustomWell) -> float:
    logger.info('Calculating Semi Metocean factor for CustomSemiRig(pk=%s) and CustomWell(pk=%s)', rig.pk, well.pk)
    rig_subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(rig)
    return calculate_semi_metocean_factor(
        metocean_days_above_hs_5=well.metocean_days_above_hs_5, wow_score=rig_subarea_score.wow
    )


def calculate_semi_well_operational_days(
    # Semi CO2 pr well
    *,
    # $AD$1, $BI$1
    reference_operational_days: float,
    # K
    efficiency: float,
    # Metocean factor'!C
    weather_factor: float,
) -> float:
    # AG=((1-K)/1,5)+'Metocean factor'!C
    # BL=((1-K)/1,5)+'Metocean factor'!C
    rig_efficiency_and_weather_factor = ((1 - efficiency) / 1.5) + weather_factor
    # AD=$AD$1*(1+AG)
    # BI=$BI$1*(1+BL)
    operational_days = reference_operational_days * (1 + rig_efficiency_and_weather_factor)
    return operational_days


def calculate_semi_well_reference_operational_days(
    # Semi CO2 pr well
    *,
    # AD, BI
    operational_days: float,
    # K
    efficiency: float,
    # Metocean factor'!C
    weather_factor: float,
) -> float:
    # AG=((1-K)/1,5)+'Metocean factor'!C
    # BL=((1-K)/1,5)+'Metocean factor'!C
    rig_efficiency_and_weather_factor = ((1 - efficiency) / 1.5) + weather_factor
    # $AD$1, $BI$1
    reference_operational_days = operational_days / (1 + rig_efficiency_and_weather_factor)
    return reference_operational_days


class SemiCO2PerWellResult(TypedDict):
    operational_days: float
    transit_time: float
    total_days: float
    rig_day_rate_usd_d: float
    spread_cost: float
    rig_fuel_per_day: float
    rig_total_fuel: float
    rig_total_co2: float
    psv_trips: float
    psv_fuel: float
    psv_co2: float
    psv_cost_usd: float
    helicopter_trips: float
    helicopter_fuel: float
    helicopter_co2: float
    helicopter_cost_usd: float
    ahv_fuel: float
    ahv_cost: float
    transit_fuel: float
    tugs: float
    tugs_cost: float
    total_fuel: float
    total_co2: float
    total_cost: float
    logistic_cost: float
    move_cost: float
    total_rig_and_spread_cost: float
    total_fuel_cost: float
    transit_co2: float
    support_co2: float


def calculate_semi_dp_co2_per_well(
    # Semi CO2 pr well
    *,
    # AD
    operational_days: float,
    # AE,'Semi Transit'!M10
    transit_time: float,
    # AH
    rig_day_rate_usd_d: float,
    # AI
    spread_cost: float,
    # AJ,O
    rig_fuel_per_day: float,
    # 'Comparison input'!$A$42
    co2_emission_per_tonne_fuel: float,
    # PSV!$B$4
    psv_visits_per_7_days: float,
    # F='Semi Deck Efficiency'!C
    deck_efficiency: float,
    # PSV!$B$19
    psv_fuel_per_trip: float,
    # PSV!$B$7
    psv_time_per_trip_d: float,
    # PSV!$B$11
    psv_fuel_cost_usd_t: float,
    # 'Comparison input'!A50, PSV!$B$12
    psv_day_rate: float,
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
    # AV,'Semi Transit'!L
    transit_fuel: float,
    # 'Comparison input'!$A$32
    marine_diesel_oil_price_usd_t: float,
    # 'Comparison input'!$A$38
    total_fuel_price: float,
    # 'Comparison input'!$A$56
    helicopter_co2_emission_per_tonne_fuel: float,
) -> SemiCO2PerWellResult:
    logger.info('Calculating Semi DP CO2 per well')
    # AF=AD+AE
    total_days = operational_days + transit_time
    # AK=AJ*AD
    rig_total_fuel = rig_fuel_per_day * operational_days
    # AL=AK*'Comparison input'!$A$42
    rig_total_co2 = rig_total_fuel * co2_emission_per_tonne_fuel
    # AM=PSV!$B$4*(AF/7)+(1-F)*AF*0,1
    psv_trips = psv_visits_per_7_days * (total_days / 7) + (1 - deck_efficiency) * total_days * 0.1
    # AN=AM*PSV!$B$19
    psv_fuel = psv_trips * psv_fuel_per_trip
    # AO=AN*'Comparison input'!$A$42
    psv_co2 = psv_fuel * co2_emission_per_tonne_fuel
    # AP=AM*PSV!$B$7*PSV!$B$12+AN*PSV!$B$11
    psv_cost_usd = psv_trips * psv_time_per_trip_d * psv_day_rate + psv_fuel * psv_fuel_cost_usd_t
    # AQ=(AF*Helicopter!$B$2)/7*Helicopter!C
    total_helicopter_trips = (total_days * helicopter_trips_per_7_days) / 7 * helicopter_factor
    # AR=Helicopter!$B$13*AQ
    total_helicopter_fuel = helicopter_fuel_consumption_per_trip_t * total_helicopter_trips
    # AS=AR*'Comparison input'!$A$56
    total_helicopter_co2 = total_helicopter_fuel * helicopter_co2_emission_per_tonne_fuel
    # AT=AR*Helicopter!$B$7+AQ*Helicopter!$B$8
    helicopter_cost_usd = (
        total_helicopter_fuel * helicopter_fuel_cost_usd_t + total_helicopter_trips * helicopter_charter_price_usd
    )
    # AU
    ahv_fuel = 0
    ahv_cost = 0
    # AU *'Comparison input'!$A$42
    ahv_co2 = ahv_fuel * co2_emission_per_tonne_fuel
    # AW
    tugs = 0
    tugs_cost = 0
    # BE=AV*'Comparison input'!$A$42
    total_transit_co2 = transit_fuel * co2_emission_per_tonne_fuel
    # AX=AK+AN+AR+AU+AV
    total_fuel = rig_total_fuel + psv_fuel + total_helicopter_fuel + ahv_fuel + transit_fuel
    # AY=AL + AO + AS + AU *'Comparison input'!$A$42 + BE
    total_co2 = rig_total_co2 + psv_co2 + total_helicopter_co2 + ahv_co2 + total_transit_co2
    # AZ=(AH+AI)*(AD+AE)+(AK+AV)*'Comparison input'!$A$32+AP+AT
    total_cost = (
        ((rig_day_rate_usd_d + spread_cost) * (operational_days + transit_time))
        + ((rig_total_fuel + transit_fuel) * marine_diesel_oil_price_usd_t)
        + psv_cost_usd
        + helicopter_cost_usd
    )
    # BA=AP+AT
    logistic_cost = psv_cost_usd + helicopter_cost_usd
    # BB=AE*(AH+AI)+AV*'Comparison input'!$A$38
    total_move_cost = transit_time * (rig_day_rate_usd_d + spread_cost) + transit_fuel * total_fuel_price
    # BC=(AH+AI)*(AF)
    total_rig_and_spread_cost = (rig_day_rate_usd_d + spread_cost) * total_days
    # BD=AX*'Comparison input'!$A$38
    total_fuel_cost = total_fuel * total_fuel_price
    # BF=AO+AS
    support_co2 = psv_co2 + total_helicopter_co2
    logger.info('Calculated Semi DP CO2 per well')
    return SemiCO2PerWellResult(
        operational_days=operational_days,
        transit_time=transit_time,
        total_days=total_days,
        rig_day_rate_usd_d=rig_day_rate_usd_d,
        spread_cost=spread_cost,
        rig_fuel_per_day=rig_fuel_per_day,
        rig_total_fuel=rig_total_fuel,
        rig_total_co2=rig_total_co2,
        psv_trips=psv_trips,
        psv_fuel=psv_fuel,
        psv_co2=psv_co2,
        psv_cost_usd=psv_cost_usd,
        helicopter_trips=total_helicopter_trips,
        helicopter_fuel=total_helicopter_fuel,
        helicopter_co2=total_helicopter_co2,
        helicopter_cost_usd=helicopter_cost_usd,
        ahv_fuel=ahv_fuel,
        ahv_cost=ahv_cost,
        transit_fuel=transit_fuel,
        tugs=tugs,
        tugs_cost=tugs_cost,
        total_fuel=total_fuel,
        total_co2=total_co2,
        total_cost=total_cost,
        logistic_cost=logistic_cost,
        move_cost=total_move_cost,
        total_rig_and_spread_cost=total_rig_and_spread_cost,
        total_fuel_cost=total_fuel_cost,
        transit_co2=total_transit_co2,
        support_co2=support_co2,
    )


def calculate_custom_semi_well_operational_days(
    *, plan: Plan, rig: CustomSemiRig, plan_well: PlanWellRelation
) -> float:
    logger.info(
        'Calculating operational days for Plan(pk=%s), CustomSemiRig(pk=%s) and PlanWellRelation(pk=%s)',
        plan.pk,
        rig.pk,
        plan_well.pk,
    )
    if plan.reference_operation_semi == rig:
        operational_days = plan_well.operational_time
    else:
        weather_factor = calculate_custom_semi_metocean_factor(rig=rig, well=plan_well.well)
        rig_efficiency = CustomSemiSubareaScore.objects.get_or_calculate(rig).efficiency
        reference_operational_days = calculate_well_reference_operational_days(plan=plan, plan_well=plan_well)
        operational_days = calculate_semi_well_operational_days(
            efficiency=rig_efficiency,
            reference_operational_days=reference_operational_days,
            weather_factor=weather_factor,
        )
    logger.info(f'Calculated {operational_days} operational days')
    return operational_days


def calculate_custom_semi_dp_co2_per_well(
    plan: Plan, plan_well: PlanWellRelation, rig: CustomSemiRig
) -> SemiCO2PerWellResult:
    logger.info(
        'Calculating Semi DP CO2 per well for Plan(pk=%s), PlanWellRelation(pk=%s) and CustomSemiRig(pk=%s)',
        plan.pk,
        plan_well.pk,
        rig.pk,
    )
    project = plan.project
    rig_subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(rig)
    common_co2_per_well = calculate_custom_semi_common_co2_per_well(rig=rig)
    operational_days = calculate_custom_semi_well_operational_days(
        plan=plan,
        rig=rig,
        plan_well=plan_well,
    )
    semi_transit = calculate_custom_semi_transit(rig=rig, plan_well=plan_well)
    total_days = operational_days + semi_transit['total_move_time']
    psv = calculate_custom_psv(
        plan_well=plan_well,
        days=total_days,
    )
    helicopter = calculate_custom_helicopter(
        rig=rig,
        plan_well=plan_well,
        days=total_days,
    )

    return calculate_semi_dp_co2_per_well(
        operational_days=operational_days,
        transit_time=semi_transit['total_move_time'],
        rig_day_rate_usd_d=rig.day_rate or 0,
        spread_cost=rig.spread_cost or 0,
        rig_fuel_per_day=common_co2_per_well['fuel'],
        co2_emission_per_tonne_fuel=project.co2_emission_per_tonne_fuel,
        psv_visits_per_7_days=project.psv_calls_per_week,
        deck_efficiency=rig_subarea_score.deck_efficiency,
        psv_fuel_per_trip=psv['fuel_consumption_per_trip'],
        psv_time_per_trip_d=psv['time_per_trip_d'],
        psv_fuel_cost_usd_t=project.psv_fuel_price,
        psv_day_rate=project.psv_day_rate,
        helicopter_trips_per_7_days=project.helicopter_no_flights_per_week,
        helicopter_factor=helicopter['factor'],
        helicopter_fuel_consumption_per_trip_t=helicopter['fuel_consumption_roundtrip_t'],
        helicopter_fuel_cost_usd_t=project.helicopter_fuel_price,
        helicopter_charter_price_usd=project.helicopter_rate_per_trip,
        transit_fuel=semi_transit['total_fuel'],
        marine_diesel_oil_price_usd_t=project.marine_diesel_oil_price,
        total_fuel_price=project.fuel_total_price,
        helicopter_co2_emission_per_tonne_fuel=HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL,
    )


def calculate_semi_ata_co2_per_well(
    *,
    # BI
    operational_days: float,
    # BJ, 'Semi Transit'!M
    transit_time: float,
    # BM
    rig_day_rate_usd_d: float,
    # BN
    spread_cost: float,
    # BO, V
    rig_fuel_per_day: float,
    # 'Comparison input'!$A$42
    co2_emission_per_tonne_fuel: float,
    # PSV!$B$4
    psv_visits_per_7_days: float,
    # F, 'Semi Deck Efficiency'!C
    deck_efficiency: float,
    # PSV!$B$19
    psv_fuel_per_trip: float,
    # PSV!$B$7
    psv_time_per_trip_d: float,
    # PSV!$B$11
    psv_fuel_cost_usd_t: float,
    # 'Comparison input'!A50, PSV!$B$12
    psv_day_rate: float,
    # Helicopter!$B$2
    helicopter_trips_per_7_days: float,
    # Helicopter!C
    helicopter_factor: float,
    # Helicopter!$B$13
    helicopter_fuel_consumption_per_trip_t: float,
    # 'Comparison input'!$A$56
    helicopter_co2_emission_per_tonne_fuel: float,
    # Helicopter!$B$7
    helicopter_fuel_cost_usd_t: float,
    # Helicopter!$B$8
    helicopter_charter_price_usd: float,
    # BZ, AHV!$B$8
    ahv_fuel: float,
    # 'Comparison input'!$A$32
    marine_diesel_oil_price_usd_t: float,
    # AHV!$B$11, 'Comparison input'!A52
    ahv_day_rate: float,
    # AHV!$B$7
    ahv_days_per_location: float,
    # CB,'Semi Transit'!L
    transit_fuel: float,
    # CC
    number_of_tugs: int,
    # 'Comparison input'!$A$46
    tugs_day_rate: float,
    # 'Comparison input'!$A$38
    total_fuel_price: float,
) -> SemiCO2PerWellResult:
    logger.info('Calculating Semi ATA CO2 per well')
    # BK=BI+BJ
    total_days = operational_days + transit_time
    # BP=BO*BI
    rig_total_fuel = rig_fuel_per_day * operational_days
    # BQ=BP*'Comparison input'!$A$42
    rig_total_co2 = rig_total_fuel * co2_emission_per_tonne_fuel
    # BR=PSV!$B$4*(BK/7)+(1-F)*BK*0,1
    psv_trips = psv_visits_per_7_days * (total_days / 7) + (1 - deck_efficiency) * total_days * 0.1
    # BS=BR*PSV!$B$19
    psv_fuel = psv_trips * psv_fuel_per_trip
    # BT=BS*'Comparison input'!$A$42
    psv_co2 = psv_fuel * co2_emission_per_tonne_fuel
    # BU=BR*PSV!$B$7*PSV!$B$12+BS*PSV!$B$11
    psv_cost_usd = psv_trips * psv_time_per_trip_d * psv_day_rate + psv_fuel * psv_fuel_cost_usd_t
    # BV=(BK*Helicopter!$B$2)/7*Helicopter!C
    helicopter_trips = (total_days * helicopter_trips_per_7_days) / 7 * helicopter_factor
    # BW=Helicopter!$B$13*BV
    helicopter_fuel = helicopter_fuel_consumption_per_trip_t * helicopter_trips
    # BX=BW*'Comparison input'!$A$56
    helicopter_co2 = helicopter_fuel * helicopter_co2_emission_per_tonne_fuel
    # BY=BW*Helicopter!$B$7+'Semi CO2 pr well'!BV*Helicopter!$B$8
    helicopter_cost_usd = helicopter_fuel * helicopter_fuel_cost_usd_t + helicopter_trips * helicopter_charter_price_usd
    # CA=BZ*'Comparison input'!$A$32+AHV!$B$11*AHV!$B$7
    ahv_cost = ahv_fuel * marine_diesel_oil_price_usd_t + ahv_day_rate * ahv_days_per_location
    # BZ*'Comparison input'!$A$42
    ahv_co2 = ahv_fuel * co2_emission_per_tonne_fuel
    # CD=Comparison input'!$A$46*CC
    tugs_cost = tugs_day_rate * number_of_tugs
    # CE=BP+BS+BW+BZ+CB
    total_fuel = rig_total_fuel + psv_fuel + helicopter_fuel + ahv_fuel + transit_fuel
    # CL=CB*'Comparison input'!$A$42
    transit_co2 = transit_fuel * co2_emission_per_tonne_fuel
    # CF=BQ + BT + BX + (BZ*'Comparison input'!$A$42) + CL
    total_co2 = rig_total_co2 + psv_co2 + helicopter_co2 + ahv_co2 + transit_co2
    # CG=(BM+BN)*(BI+BJ)+(BP+CB)*'Comparison input'!$A$32+BU+BY+CA+CD
    total_cost = (
        (rig_day_rate_usd_d + spread_cost) * (operational_days + transit_time)
        + (rig_total_fuel + transit_fuel) * marine_diesel_oil_price_usd_t
        + psv_cost_usd
        + helicopter_cost_usd
        + ahv_cost
        + tugs_cost
    )
    # CH=BU+BY
    logistic_cost = psv_cost_usd + helicopter_cost_usd
    # CI=CA+CD+BJ*(BM+BN)+CB*'Comparison input'!$A$38
    move_cost = (
        ahv_cost + tugs_cost + transit_time * (rig_day_rate_usd_d + spread_cost) + transit_fuel * total_fuel_price
    )
    # CJ=(BM+BN)*(BK)
    total_rig_and_spread_cost = (rig_day_rate_usd_d + spread_cost) * total_days
    # CK=CE*'Comparison input'!$A$38
    total_fuel_cost = total_fuel * total_fuel_price
    # CM=BT+BX
    support_co2 = psv_co2 + helicopter_co2
    logger.info('Calculated Semi ATA CO2 per well')

    return SemiCO2PerWellResult(
        operational_days=operational_days,
        transit_time=transit_time,
        total_days=total_days,
        rig_day_rate_usd_d=rig_day_rate_usd_d,
        spread_cost=spread_cost,
        rig_fuel_per_day=rig_fuel_per_day,
        rig_total_fuel=rig_total_fuel,
        rig_total_co2=rig_total_co2,
        psv_trips=psv_trips,
        psv_fuel=psv_fuel,
        psv_co2=psv_co2,
        psv_cost_usd=psv_cost_usd,
        helicopter_trips=helicopter_trips,
        helicopter_fuel=helicopter_fuel,
        helicopter_co2=helicopter_co2,
        helicopter_cost_usd=helicopter_cost_usd,
        ahv_fuel=ahv_fuel,
        ahv_cost=ahv_cost,
        transit_fuel=transit_fuel,
        tugs=number_of_tugs,
        tugs_cost=tugs_cost,
        total_fuel=total_fuel,
        total_co2=total_co2,
        total_cost=total_cost,
        logistic_cost=logistic_cost,
        move_cost=move_cost,
        total_rig_and_spread_cost=total_rig_and_spread_cost,
        total_fuel_cost=total_fuel_cost,
        transit_co2=transit_co2,
        support_co2=support_co2,
    )


def calculate_ahv_fuel_consumption_per_location(
    *,
    # B2
    ahv_fuel_consumption_td: float,
    # B7
    ahv_days_per_location: float,
) -> float:
    # B8=B2*B7
    return ahv_fuel_consumption_td * ahv_days_per_location


def calculate_custom_ahv_fuel_consumption_per_location(project: Project) -> float:
    # B8=B2*B7
    return calculate_ahv_fuel_consumption_per_location(
        ahv_fuel_consumption_td=project.ahv_avg_fuel_consumption, ahv_days_per_location=project.ahv_no_days_per_location
    )


def calculate_custom_semi_ata_co2_per_well(
    plan: Plan, plan_well: PlanWellRelation, rig: CustomSemiRig
) -> SemiCO2PerWellResult:
    logger.info(
        'Calculating Semi ATA CO2 per well for Plan(pk=%s), PlanWellRelation(pk=%s) and CustomSemiRig(pk=%s)',
        plan.pk,
        plan_well.pk,
        rig.pk,
    )
    project = plan.project
    rig_subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(rig)
    operational_days = calculate_custom_semi_well_operational_days(
        plan=plan,
        rig=rig,
        plan_well=plan_well,
    )
    semi_transit = calculate_custom_semi_transit(rig=rig, plan_well=plan_well)
    total_days = operational_days + semi_transit['total_move_time']
    psv = calculate_custom_psv(
        plan_well=plan_well,
        days=total_days,
    )
    helicopter = calculate_custom_helicopter(
        rig=rig,
        plan_well=plan_well,
        days=total_days,
    )
    common_co2_per_well = calculate_custom_semi_common_co2_per_well(rig=rig)
    ahv_fuel_consumption_per_location = calculate_custom_ahv_fuel_consumption_per_location(project)

    return calculate_semi_ata_co2_per_well(
        operational_days=operational_days,
        transit_time=semi_transit['total_move_time'],
        rig_day_rate_usd_d=rig.day_rate or 0,
        spread_cost=rig.spread_cost or 0,
        rig_fuel_per_day=common_co2_per_well['fuel'],
        co2_emission_per_tonne_fuel=project.co2_emission_per_tonne_fuel,
        psv_visits_per_7_days=project.psv_calls_per_week,
        deck_efficiency=rig_subarea_score.deck_efficiency,
        psv_fuel_per_trip=psv['fuel_consumption_per_trip'],
        psv_time_per_trip_d=psv['time_per_trip_d'],
        psv_fuel_cost_usd_t=project.psv_fuel_price,
        psv_day_rate=project.psv_day_rate,
        helicopter_trips_per_7_days=project.helicopter_no_flights_per_week,
        helicopter_factor=helicopter['factor'],
        helicopter_fuel_consumption_per_trip_t=helicopter['fuel_consumption_roundtrip_t'],
        helicopter_co2_emission_per_tonne_fuel=HELICOPTER_CO2_EMISSION_PER_TONNE_FUEL,
        helicopter_fuel_cost_usd_t=project.helicopter_fuel_price,
        helicopter_charter_price_usd=project.helicopter_rate_per_trip,
        transit_fuel=semi_transit['total_fuel'],
        marine_diesel_oil_price_usd_t=project.marine_diesel_oil_price,
        total_fuel_price=project.fuel_total_price,
        ahv_fuel=ahv_fuel_consumption_per_location,
        ahv_day_rate=project.ahv_day_rate,
        ahv_days_per_location=project.ahv_no_days_per_location,
        number_of_tugs=rig.tugs_no_used,
        tugs_day_rate=project.tugs_day_rate,
    )


def calculate_custom_semi_co2_per_well(
    plan: Plan, plan_well: PlanWellRelation, rig: CustomSemiRig
) -> SemiCO2PerWellResult:
    if rig.dp:
        return calculate_custom_semi_dp_co2_per_well(plan=plan, plan_well=plan_well, rig=rig)
    elif rig.thruster_assist:
        return calculate_custom_semi_ata_co2_per_well(plan=plan, plan_well=plan_well, rig=rig)
    raise NotImplementedError('Custom Semi rigs with passive positioning are not supported')
