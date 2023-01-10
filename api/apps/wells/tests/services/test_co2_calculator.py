from datetime import datetime, timedelta
from typing import cast
from unittest import mock

import pytest

from apps.emissions.factories import (
    AssetFactory,
    BaselineInputFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionReductionInitiativeInputFactory,
    ExternalEnergySupplyFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    WellCompleteStepMaterialFactory,
    WellPlannedStepMaterialFactory,
)
from apps.emissions.models import AssetSeason, EmissionReductionInitiativeType, MaterialCategory, PlannedHelicopterUse
from apps.monitors.factories import MonitorFunctionFactory, MonitorFunctionValueFactory
from apps.monitors.models import MonitorFunctionType
from apps.wells.factories import WellPlannerCompleteStepFactory, WellPlannerFactory, WellPlannerPlannedStepFactory
from apps.wells.models import WellPlannerWizardStep
from apps.wells.services.co2calculator import (
    HelicopterOperation,
    VesselOperation,
    WellPlannerStepCO2EmissionReductionInitiative,
    WellPlannerStepCO2Result,
    calculate_measured_well_planner_step_base_co2,
    calculate_measured_well_planner_step_co2,
    calculate_measured_well_planner_step_rig_co2,
    calculate_phase_base_co2,
    calculate_phase_baseline_co2,
    calculate_phase_cement_co2,
    calculate_phase_emp_improvement_co2,
    calculate_phase_external_energy_supply_co2,
    calculate_phase_helicopters_co2,
    calculate_phase_improved_duration,
    calculate_phase_rig_co2,
    calculate_phase_steel_co2,
    calculate_phase_target_line_co2,
    calculate_phase_vessels_co2,
    calculate_planned_step_improved_duration,
    calculate_well_planner_co2_improvement,
    calculate_well_planner_step_base_co2,
    calculate_well_planner_step_cement_co2,
    calculate_well_planner_step_co2,
    calculate_well_planner_step_emission_reduction_initiative_improvements,
    calculate_well_planner_step_external_energy_supply_co2,
    calculate_well_planner_step_helicopters_co2,
    calculate_well_planner_step_rig_co2,
    calculate_well_planner_step_steel_co2,
    calculate_well_planner_step_vessels_co2,
    get_vessel_fuel_consumption,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, input, output',
    (
        (
            'Sikorsky S-92',
            dict(
                phase_duration=10,
                total_duration=37.05,
                co2_factor=3.16,
                helicopters=[HelicopterOperation(8, 180, 641)],
            ),
            10.496829149797573,
        ),
        (
            'SuperPuma',
            dict(
                phase_duration=10,
                total_duration=37.05,
                co2_factor=3.16,
                helicopters=[
                    HelicopterOperation(8, 180, 650),
                ],
            ),
            10.644210526315792,
        ),
        (
            'Sikorsky S-92 and SuperPuma',
            dict(
                phase_duration=10,
                total_duration=37.05,
                co2_factor=3.16,
                helicopters=[
                    HelicopterOperation(8, 180, 641),
                    HelicopterOperation(8, 180, 650),
                ],
            ),
            21.141039676113365,
        ),
    ),
)
def test_calculate_phase_helicopters_co2(name, input, output):
    assert calculate_phase_helicopters_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                phase_duration=10,
                fuel_consumption=25,
                co2_factor=3.17,
            ),
            792.5,
        ),
        (
            dict(
                phase_duration=7.3,
                fuel_consumption=25,
                co2_factor=3.17,
            ),
            578.525,
        ),
    ),
)
def test_calculate_phase_base_co2(input, output):
    assert calculate_phase_base_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                base_co2=840,
                emission_reduction_initiatives_improvement=386.4,
            ),
            453.6,
        ),
        (
            dict(
                base_co2=766.5,
                emission_reduction_initiatives_improvement=352.59,
            ),
            413.91,
        ),
        (
            dict(
                base_co2=766.5,
                emission_reduction_initiatives_improvement=160.965,
            ),
            605.535,
        ),
        (
            dict(
                base_co2=766.5,
                emission_reduction_initiatives_improvement=321.93,
            ),
            444.57,
        ),
    ),
)
def test_calculate_phase_rig_co2(input, output):
    assert calculate_phase_rig_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                improvement=21,
                base_co2=840,
            ),
            176.4,
        ),
        (
            dict(
                improvement=0,
                base_co2=840,
            ),
            0,
        ),
        (
            dict(
                improvement=21,
                base_co2=766.5,
            ),
            160.965,
        ),
        (
            dict(
                improvement=0,
                base_co2=766.5,
            ),
            0,
        ),
    ),
)
def test_calculate_phase_emp_improvement_co2(input, output):
    assert calculate_phase_emp_improvement_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                phase_duration=10,
                total_duration=37.05,
                co2_factor=3.17,
                vessels=[
                    VesselOperation(12, 7),
                    VesselOperation(11, 5),
                    VesselOperation(11, 31.55),
                    VesselOperation(10, 5),
                    VesselOperation(9, 3),
                ],
            ),
            481.7458839406208,
        ),
        (
            dict(
                phase_duration=7.3,
                total_duration=37.05,
                co2_factor=3.17,
                vessels=[
                    VesselOperation(12, 7),
                    VesselOperation(11, 5),
                    VesselOperation(11, 31.55),
                    VesselOperation(10, 5),
                    VesselOperation(9, 3),
                ],
            ),
            351.67449527665315,
        ),
    ),
)
def test_calculate_phase_vessels_co2(input, output):
    assert calculate_phase_vessels_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                phase_duration=8.70,
                capacity=2000,
                co2_factor=0.000201,
            ),
            83.93759999999999,
        ),
        (
            dict(
                phase_duration=6.351,
                capacity=2000,
                co2_factor=0.000201,
            ),
            61.274448,
        ),
        (
            dict(
                phase_duration=10,
                capacity=2000,
                co2_factor=0.000201,
            ),
            96.47999999999999,
        ),
    ),
)
def test_calculate_phase_external_energy_supply_co2(input, output):
    assert calculate_phase_external_energy_supply_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                phase_duration=10,
                productivity_improvement=13,
            ),
            8.70,
        ),
        (
            dict(
                phase_duration=7.3,
                productivity_improvement=13,
            ),
            6.351,
        ),
    ),
)
def test_calculate_phase_improved_duration(input, output):
    assert calculate_phase_improved_duration(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                base_co2=840,
                cement_co2=0,
                steel_co2=0,
                external_energy_supply_co2=83.9376,
                vessels_co2=96.3491767881242,
                helicopters_co2=109.467206477733,
            ),
            1129.7539832658572,
        ),
        (
            dict(
                base_co2=766.5,
                cement_co2=162,
                steel_co2=92.5,
                external_energy_supply_co2=61.274448,
                vessels_co2=351.674495276653,
                helicopters_co2=68.417004048583,
            ),
            1502.3659473252358,
        ),
        (
            dict(
                base_co2=766.5,
                cement_co2=162.0,
                steel_co2=92.5,
                external_energy_supply_co2=96.47999999999999,
                vessels_co2=481.7458839406208,
                helicopters_co2=21.141039676113365,
            ),
            1620.366923616734,
        ),
    ),
)
def test_calculate_phase_baseline_co2(input, output):
    assert calculate_phase_baseline_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                rig_co2=453.6,
                cement_co2=0,
                steel_co2=0,
                external_energy_supply_co2=83.9376,
                vessels_co2=96.3491767881242,
                helicopters_co2=109.467206477733,
            ),
            743.3539832658572,
        ),
        (
            dict(
                rig_co2=413.91,
                cement_co2=162,
                steel_co2=92.5,
                external_energy_supply_co2=61.274448,
                vessels_co2=351.674495276653,
                helicopters_co2=68.417004048583,
            ),
            1149.775947325236,
        ),
        (
            dict(
                rig_co2=444.57,
                cement_co2=162.0,
                steel_co2=92.5,
                external_energy_supply_co2=96.47999999999999,
                vessels_co2=481.7458839406208,
                helicopters_co2=21.141039676113365,
            ),
            1298.4369236167342,
        ),
    ),
)
def test_calculate_phase_target_line_co2(input, output):
    assert calculate_phase_target_line_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                cement=0,
                co2_factor=0.81,
            ),
            0,
        ),
        (
            dict(
                cement=200,
                co2_factor=0.81,
            ),
            162,
        ),
    ),
)
def test_calculate_phase_cement_co2(input, output):
    assert calculate_phase_cement_co2(**input) == output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'input, output',
    (
        (
            dict(
                steel=0,
                co2_factor=1.85,
            ),
            0,
        ),
        (
            dict(
                steel=50,
                co2_factor=1.85,
            ),
            92.5,
        ),
    ),
)
def test_calculate_phase_steel_co2(input, output):
    assert calculate_phase_steel_co2(**input) == output


@pytest.mark.django_db
def test_calculate_well_planner_planned_step_improved_duration():
    phase = CustomPhaseFactory()
    mode = CustomModeFactory()
    emp_1_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=10,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.PRODUCTIVITY,
    )
    emp_2_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=15,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.PRODUCTIVITY,
    )
    emp_3_phase = EmissionReductionInitiativeInputFactory(
        phase=phase, mode=mode, value=20, emission_reduction_initiative__type=EmissionReductionInitiativeType.BASELOADS
    )
    EmissionReductionInitiativeInputFactory(
        value=10, emission_reduction_initiative__type=EmissionReductionInitiativeType.PRODUCTIVITY
    )

    well_planner_step = WellPlannerPlannedStepFactory(
        duration=5,
        waiting_on_weather=100,
        phase=phase,
        mode=mode,
    )
    well_planner_step.emission_reduction_initiatives.set(
        [
            emp_1_phase.emission_reduction_initiative,
            emp_2_phase.emission_reduction_initiative,
            emp_3_phase.emission_reduction_initiative,
        ]
    )

    assert calculate_planned_step_improved_duration(well_planner_step) == 7.5


@pytest.mark.django_db
def test_calculate_well_planner_step_base_co2():
    baseline_input = BaselineInputFactory(value=25.0)
    well_planner_step = WellPlannerPlannedStepFactory(
        phase=baseline_input.phase,
        mode=baseline_input.mode,
        season=baseline_input.season,
        duration=10,
        well_planner__baseline=baseline_input.baseline,
    )

    base_co2 = calculate_well_planner_step_base_co2(
        well_planner_step=well_planner_step,
        duration=well_planner_step.duration,
    )

    assert base_co2 == 792.5


@pytest.mark.django_db
@pytest.mark.parametrize(
    'well_planner_step_data,output',
    (
        (
            dict(
                duration=8.70,
                external_energy_supply_enabled=True,
            ),
            83.93759999999999,
        ),
        (
            dict(
                duration=6.351,
                external_energy_supply_enabled=True,
            ),
            61.274448,
        ),
        (
            dict(
                duration=10.0,
                external_energy_supply_enabled=True,
            ),
            96.47999999999999,
        ),
        (
            dict(
                duration=10.0,
                external_energy_supply_enabled=False,
            ),
            0,
        ),
        (
            dict(
                duration=10.0,
                external_energy_supply_enabled=False,
            ),
            0,
        ),
    ),
)
def test_calculate_well_planner_step_external_energy_supply_co2(well_planner_step_data: dict, output: float):
    well_planner_step = WellPlannerPlannedStepFactory(**well_planner_step_data)
    ExternalEnergySupplyFactory(asset=well_planner_step.well_planner.asset, capacity=2000, co2=0.000201)

    external_energy_supply_co2 = calculate_well_planner_step_external_energy_supply_co2(
        well_planner_step=well_planner_step, duration=well_planner_step.duration
    )

    assert external_energy_supply_co2 == output


@pytest.mark.django_db
def test_calculate_well_planner_step_cement_co2():
    well_planner_step = WellPlannerPlannedStepFactory()

    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.CEMENT, quantity=0, material_type__co2=0.81, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.CEMENT, quantity=200, material_type__co2=0.81, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.CEMENT, quantity=200, material_type__co2=0.81, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=200, material_type__co2=0.81, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=200, material_type__co2=0.81
    )

    assert calculate_well_planner_step_cement_co2(well_planner_step) == 324


@pytest.mark.django_db
def test_calculate_well_planner_step_steel_co2():
    well_planner_step = WellPlannerPlannedStepFactory()

    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=0, material_type__co2=1.85, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=50, material_type__co2=1.85, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=50, material_type__co2=1.85, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.CEMENT, quantity=999, material_type__co2=999, step=well_planner_step
    )
    WellPlannedStepMaterialFactory(
        material_type__category=MaterialCategory.STEEL, quantity=200, material_type__co2=0.81
    )

    assert calculate_well_planner_step_steel_co2(well_planner_step) == 185


@pytest.mark.django_db
def test_calculate_well_planner_step_helicopters_co2():
    well_planner = WellPlannerFactory()
    PlannedHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=641,
    )
    PlannedHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=650,
    )

    helicopters_co2 = calculate_well_planner_step_helicopters_co2(
        helicopter_uses=PlannedHelicopterUse.objects.all(), duration=10, total_duration=37.05
    )

    assert helicopters_co2 == 21.141039676113365


@pytest.mark.django_db
def test_calculate_well_planner_step_vessels_co2():
    well_planner = WellPlannerFactory()
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=7,
        duration=6,
        waiting_on_weather=100,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=11,
        waiting_on_weather=0,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=31.55,
        duration=11,
        waiting_on_weather=0,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=5,
        waiting_on_weather=100,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=3,
        duration=6,
        waiting_on_weather=50,
        season=AssetSeason.SUMMER,
    )

    well_planner_step = WellPlannerPlannedStepFactory(well_planner=well_planner, season=AssetSeason.SUMMER)
    vessel_operations = [
        VesselOperation(
            vessel_use.total_days,
            get_vessel_fuel_consumption(
                vessel_type=vessel_use.vessel_type, season=cast(AssetSeason, well_planner_step.season)
            ),
        )
        for vessel_use in well_planner_step.well_planner.plannedvesseluse_set.all()
    ]

    vessels_co2 = calculate_well_planner_step_vessels_co2(
        vessel_operations=vessel_operations,
        duration=10,
        total_season_duration=37.05,
    )

    assert vessels_co2 == 481.7458839406208


@pytest.mark.django_db
def test_calculate_well_planner_step_emp_improvements():
    phase = CustomPhaseFactory()
    mode = CustomModeFactory()
    emission_reduction_initiative_1_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=21.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.BASELOADS,
    )
    emission_reduction_initiative_2_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=15.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.POWER_SYSTEMS,
    )
    emission_reduction_initiative_3_phase = EmissionReductionInitiativeInputFactory(
        mode=mode, value=4.0, emission_reduction_initiative__type=EmissionReductionInitiativeType.POWER_SYSTEMS
    )
    emission_reduction_initiative_4_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=10.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.PRODUCTIVITY,
    )
    well_planner_step = WellPlannerPlannedStepFactory(
        phase=phase,
        mode=mode,
    )
    well_planner_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_1_phase.emission_reduction_initiative,
        emission_reduction_initiative_2_phase.emission_reduction_initiative,
        emission_reduction_initiative_3_phase.emission_reduction_initiative,
        emission_reduction_initiative_4_phase.emission_reduction_initiative,
    )

    base_co2 = 766.5
    emp_improvements = calculate_well_planner_step_emission_reduction_initiative_improvements(
        well_planner_step=well_planner_step, base_co2=base_co2
    )

    assert emp_improvements == [
        WellPlannerStepCO2EmissionReductionInitiative(
            emission_reduction_initiative=emission_reduction_initiative_1_phase.emission_reduction_initiative,
            value=emission_reduction_initiative_1_phase.value / 100 * base_co2,
        ),
        WellPlannerStepCO2EmissionReductionInitiative(
            emission_reduction_initiative=emission_reduction_initiative_2_phase.emission_reduction_initiative,
            value=emission_reduction_initiative_2_phase.value / 100 * base_co2,
        ),
    ]


@pytest.mark.django_db
def test_calculate_well_planner_step_rig_co2():
    rig_co2 = calculate_well_planner_step_rig_co2(
        base_co2=766.5,
        emission_reduction_initiative_improvements=[
            WellPlannerStepCO2EmissionReductionInitiative(emission_reduction_initiative=mock.ANY, value=160.965),
            WellPlannerStepCO2EmissionReductionInitiative(emission_reduction_initiative=mock.ANY, value=160.965),
        ],
    )

    assert rig_co2 == 444.57


@pytest.mark.django_db
def test_calculate_well_planner_step_co2():
    asset = AssetFactory()
    well_planner = WellPlannerFactory(asset=asset)
    phase = CustomPhaseFactory(asset=asset)
    mode = CustomModeFactory(asset=asset)
    season = AssetSeason.SUMMER
    well_planner_step = WellPlannerPlannedStepFactory(
        well_planner=well_planner,
        duration=10,
        phase=phase,
        mode=mode,
        season=season,
        external_energy_supply_enabled=True,
    )
    ExternalEnergySupplyFactory(
        asset=asset,
        capacity=2000,
        co2=0.000201,
    )
    WellPlannedStepMaterialFactory(
        step=well_planner_step,
        quantity=200.0,
        material_type__co2=0.81,
        material_type__category=MaterialCategory.CEMENT,
    )
    WellPlannedStepMaterialFactory(
        step=well_planner_step,
        quantity=50.0,
        material_type__co2=1.85,
        material_type__category=MaterialCategory.STEEL,
    )
    WellCompleteStepMaterialFactory(
        quantity=200.0,
        material_type__co2=0.81,
        material_type__category=MaterialCategory.CEMENT,
    )
    WellCompleteStepMaterialFactory(
        quantity=50.0,
        material_type__co2=1.85,
        material_type__category=MaterialCategory.STEEL,
    )
    BaselineInputFactory(
        baseline=well_planner.baseline,
        phase=phase,
        mode=mode,
        season=season,
        value=24.179810725552052,
    )
    (
        emission_reduction_initiative_1_phase,
        emission_reduction_initiative_2_phase,
    ) = EmissionReductionInitiativeInputFactory.create_batch(
        2,
        emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
        phase=phase,
        mode=mode,
        value=21.0,
    )

    well_planner_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_1_phase.emission_reduction_initiative
    )
    well_planner_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_2_phase.emission_reduction_initiative
    )

    PlannedHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=641,
    )
    PlannedHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=650,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=7,
        duration=10,
        waiting_on_weather=20,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_winter=6,
        duration=11,
        season=AssetSeason.WINTER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=11,
        waiting_on_weather=0,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=31.55,
        duration=11,
        waiting_on_weather=0,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=5,
        waiting_on_weather=100,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=3,
        duration=6,
        waiting_on_weather=50,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        vessel_type__fuel_consumption_summer=3,
        duration=6,
        waiting_on_weather=50,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        vessel_type__fuel_consumption_summer=3,
        duration=6,
        season=AssetSeason.SUMMER,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_winter=4.5,
        duration=6,
        season=AssetSeason.WINTER,
    )

    well_planner_step_co2 = calculate_well_planner_step_co2(
        planned_step=well_planner_step,
        duration=well_planner_step.duration,
        total_duration=37.05,
        total_season_duration=37.05,
    )
    assert well_planner_step_co2 == WellPlannerStepCO2Result(
        base=766.5,
        baseline=1620.366923616734,
        target=1298.4369236167342,
        rig=444.57,
        vessels=481.7458839406208,
        helicopters=21.141039676113365,
        cement=162.0,
        steel=92.5,
        external_energy_supply=96.47999999999999,
        emission_reduction_initiatives=[
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_1_phase.emission_reduction_initiative,
                value=160.965,
            ),
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_2_phase.emission_reduction_initiative,
                value=160.965,
            ),
        ],
    )


@pytest.mark.django_db
def test_calculate_well_planner_co2_improvement():
    asset = AssetFactory()
    phase = CustomPhaseFactory(asset=asset)
    mode = CustomModeFactory(asset=asset)
    well_planner = WellPlannerFactory(asset=asset)
    season = AssetSeason.SUMMER
    well_planner_step = WellPlannerPlannedStepFactory(
        well_planner=well_planner,
        duration=5,
        waiting_on_weather=100,
        improved_duration=5,
        phase=phase,
        mode=mode,
        season=season,
        external_energy_supply_enabled=True,
    )
    ExternalEnergySupplyFactory(
        asset=asset,
        capacity=2000,
        co2=0.000201,
    )
    WellPlannedStepMaterialFactory(
        step=well_planner_step,
        quantity=200.0,
        material_type__co2=0.81,
        material_type__category=MaterialCategory.CEMENT,
    )
    WellPlannedStepMaterialFactory(
        step=well_planner_step,
        quantity=50.0,
        material_type__co2=1.85,
        material_type__category=MaterialCategory.STEEL,
    )
    BaselineInputFactory(
        baseline=well_planner.baseline,
        phase=phase,
        mode=mode,
        season=season,
        value=24.179810725552052,
    )
    (
        emission_reduction_initiative_1_phase,
        emission_reduction_initiative_2_phase,
    ) = EmissionReductionInitiativeInputFactory.create_batch(
        2,
        emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
        phase=phase,
        mode=mode,
        value=21.0,
    )

    well_planner_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_1_phase.emission_reduction_initiative
    )
    well_planner_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_2_phase.emission_reduction_initiative
    )

    expected_improvement = WellPlannerStepCO2Result(
        base=766.5 / 2,
        baseline=431.49,
        target=270.525,
        rig=444.57 / 2,
        vessels=0.0,
        helicopters=0.0,
        cement=0.0,
        steel=0.0,
        external_energy_supply=96.47999999999999 / 2,
        emission_reduction_initiatives=[
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_1_phase.emission_reduction_initiative,
                value=160.965 / 2,
            ),
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_2_phase.emission_reduction_initiative,
                value=160.965 / 2,
            ),
        ],
    )

    improvement = calculate_well_planner_co2_improvement(well_planner)
    assert expected_improvement == improvement


@pytest.mark.django_db
def test_calculate_measured_well_planner_step_rig_co2():
    well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
    vessel = well_planner.asset.vessel
    WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.5)
    complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=4)
    WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1)

    monitor_function = MonitorFunctionFactory(
        vessel=vessel,
        type=MonitorFunctionType.CO2_EMISSION,
    )

    start_datetime = datetime(
        year=well_planner.actual_start_date.year,
        month=well_planner.actual_start_date.month,
        day=well_planner.actual_start_date.day,
    )

    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime,
        value=99.0,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=0.5),
        value=2.0,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=4.0),
        value=3.0,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=4.5),
        value=99.0,
    )

    rig_co2 = calculate_measured_well_planner_step_rig_co2(
        complete_step,
        start_datetime + timedelta(days=0.5),
        start_datetime + timedelta(days=4.5),
    )
    assert rig_co2 == 5.0


@pytest.mark.django_db
def test_calculate_measured_well_planner_step_base_co2():
    phase = CustomPhaseFactory()
    mode = CustomModeFactory()

    complete_step = WellPlannerCompleteStepFactory(
        duration=10,
        phase=phase,
        mode=mode,
        season=AssetSeason.SUMMER,
    )
    emission_reduction_initiative_1_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=21.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.BASELOADS,
    )
    emission_reduction_initiative_2_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=11.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.POWER_SYSTEMS,
    )
    emission_reduction_initiative_3_phase = EmissionReductionInitiativeInputFactory(
        phase=phase,
        mode=mode,
        value=13.0,
        emission_reduction_initiative__type=EmissionReductionInitiativeType.PRODUCTIVITY,
    )
    emission_reduction_initiative_4_phase = EmissionReductionInitiativeInputFactory(
        mode=mode, value=24.0, emission_reduction_initiative__type=EmissionReductionInitiativeType.BASELOADS
    )
    complete_step.emission_reduction_initiatives.set(
        [
            emission_reduction_initiative_1_phase.emission_reduction_initiative,
            emission_reduction_initiative_2_phase.emission_reduction_initiative,
            emission_reduction_initiative_3_phase.emission_reduction_initiative,
            emission_reduction_initiative_4_phase.emission_reduction_initiative,
        ]
    )

    measured_rig_co2 = 570
    base_co2 = calculate_measured_well_planner_step_base_co2(
        complete_step=complete_step,
        measured_rig_co2=measured_rig_co2,
    )
    expected_base_co2 = 838.2352941176472
    assert base_co2 == expected_base_co2
    assert (
        base_co2
        - (emission_reduction_initiative_1_phase.value + emission_reduction_initiative_2_phase.value) / 100 * base_co2
        == measured_rig_co2
    )


@pytest.mark.django_db
def test_calculate_measured_well_planner_step_co2():
    asset = AssetFactory()
    well_planner = WellPlannerFactory(asset=asset, current_step=WellPlannerWizardStep.WELL_REVIEWING)
    phase = CustomPhaseFactory(asset=asset)
    mode = CustomModeFactory(asset=asset)
    complete_step = WellPlannerCompleteStepFactory(
        well_planner=well_planner,
        duration=10,
        phase=phase,
        mode=mode,
        season=AssetSeason.SUMMER,
        external_energy_supply_enabled=True,
    )
    ExternalEnergySupplyFactory(
        asset=asset,
        capacity=2000,
        co2=0.000201,
    )
    WellCompleteStepMaterialFactory(
        step=complete_step,
        quantity=200.0,
        material_type__co2=0.81,
        material_type__category=MaterialCategory.CEMENT,
    )
    WellCompleteStepMaterialFactory(
        step=complete_step,
        quantity=50.0,
        material_type__co2=1.85,
        material_type__category=MaterialCategory.STEEL,
    )
    BaselineInputFactory(
        baseline__asset=asset,
        phase=phase,
        mode=mode,
        season=AssetSeason.SUMMER,
        value=24.179810725552052,
    )

    (
        emission_reduction_initiative_1_phase,
        emission_reduction_initiative_2_phase,
    ) = EmissionReductionInitiativeInputFactory.create_batch(
        2,
        emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
        phase=phase,
        mode=mode,
        value=21.0,
    )
    complete_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_1_phase.emission_reduction_initiative
    )
    complete_step.emission_reduction_initiatives.add(
        emission_reduction_initiative_2_phase.emission_reduction_initiative
    )

    PlannedHelicopterUseFactory(
        well_planner=well_planner,
        trips=10,
        trip_duration=200,
        helicopter_type__fuel_consumption=720,
    )
    CompleteHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=641,
    )
    CompleteHelicopterUseFactory(
        well_planner=well_planner,
        trips=8,
        trip_duration=180,
        helicopter_type__fuel_consumption=650,
    )
    PlannedVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=6,
        duration=9,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=7,
        duration=12,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=11,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=31.55,
        duration=11,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=5,
        duration=10,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_summer=3,
        duration=9,
        season=AssetSeason.SUMMER,
    )
    CompleteVesselUseFactory(
        well_planner=well_planner,
        vessel_type__fuel_consumption_winter=4,
        duration=4,
        season=AssetSeason.WINTER,
    )

    start_datetime = datetime(
        year=well_planner.actual_start_date.year,
        month=well_planner.actual_start_date.month,
        day=well_planner.actual_start_date.day,
    )

    monitor_function = MonitorFunctionFactory(
        vessel=well_planner.asset.vessel,
        type=MonitorFunctionType.CO2_EMISSION,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime,
        value=111.57,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=0.5),
        value=111,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=3),
        value=111,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=6),
        value=111,
    )
    MonitorFunctionValueFactory(
        monitor_function=monitor_function,
        date=start_datetime + timedelta(days=10),
        value=999,
    )
    MonitorFunctionValueFactory()
    MonitorFunctionValueFactory(
        monitor_function__type=MonitorFunctionType.WAVE_HEAVE,
    )
    MonitorFunctionValueFactory(
        monitor_function__type=MonitorFunctionType.AIR_TEMPERATURE,
    )
    MonitorFunctionValueFactory(
        monitor_function__type=MonitorFunctionType.WIND_SPEED,
    )

    step_co2 = calculate_measured_well_planner_step_co2(
        complete_step=complete_step,
        start=start_datetime,
        end=start_datetime + timedelta(days=10),
        total_duration=37.05,
        total_season_duration=37.05,
    )

    assert step_co2 == WellPlannerStepCO2Result(
        base=766.4999999999999,
        baseline=1620.366923616734,
        rig=444.57,
        target=1298.4369236167342,
        vessels=481.7458839406208,
        helicopters=21.141039676113365,
        cement=162.0,
        steel=92.5,
        external_energy_supply=96.47999999999999,
        emission_reduction_initiatives=[
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_1_phase.emission_reduction_initiative,
                value=160.96499999999997,
            ),
            WellPlannerStepCO2EmissionReductionInitiative(
                emission_reduction_initiative=emission_reduction_initiative_2_phase.emission_reduction_initiative,
                value=160.96499999999997,
            ),
        ],
    )
