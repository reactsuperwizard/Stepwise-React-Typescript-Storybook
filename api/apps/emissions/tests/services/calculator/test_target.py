import pytest

from apps.emissions.factories import (
    BaselineInputFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    WellPlannedStepMaterialFactory,
)
from apps.emissions.factories.assets import EmissionReductionInitiativeInputFactory, ExternalEnergySupplyFactory
from apps.emissions.models.assets import AssetSeason
from apps.emissions.services.calculator.target import (
    InitiativeReductionData,
    TargetCO2Data,
    TargetNOXData,
    calculate_planned_step_target_co2,
    calculate_planned_step_target_nox,
)
from apps.wells.factories import WellPlannerFactory, WellPlannerPlannedStepFactory
from apps.wells.models import WellPlannerPlannedStep

# v20.12.22
VESSELS = {
    "Anchor Handling Tug Supply (AHTS)": dict(
        # 'Asset & Material Inputs'!F71
        fuel_consumption=13.0,
        # 'Well Planning'!H19
        waiting_on_weather=5,
        # 'Well Planning'!F19
        duration=7.0,
        # 'Well Planning'!G19
        exposure=20,
        # 'Asset & Material Inputs'!G71
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!H71
        fuel_density=835,
        # 'Asset & Material Inputs'!I71
        nox_per_fuel=53.5,
    ),
    "Platform supply vessel (PSV)": dict(
        # 'Asset & Material Inputs'!F72
        fuel_consumption=12.0,
        # 'Well Planning'!H20
        waiting_on_weather=5,
        # 'Well Planning'!F20
        duration=5.0,
        # 'Well Planning'!G20
        exposure=70,
        # 'Asset & Material Inputs'!G72
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!H72
        fuel_density=835,
        # 'Asset & Material Inputs'!I72
        nox_per_fuel=53.5,
    ),
    "Stand by vessel (STBY)": dict(
        # 'Asset & Material Inputs'!F73
        fuel_consumption=11.5,
        # 'Well Planning'!H21
        waiting_on_weather=5,
        # 'Well Planning'!F21
        duration=18.0,
        # 'Well Planning'!G21
        exposure=90,
        # 'Asset & Material Inputs'!G73
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!H73
        fuel_density=835,
        # 'Asset & Material Inputs'!I73
        nox_per_fuel=53.5,
    ),
    "Multi purpose supply vessels (MPSV)": dict(
        # 'Asset & Material Inputs'!F74
        fuel_consumption=10.50,
        # 'Well Planning'!H22
        waiting_on_weather=5,
        # 'Well Planning'!F22
        duration=7.0,
        # 'Well Planning'!G22
        exposure=100,
        # 'Asset & Material Inputs'!G74
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!H74
        fuel_density=835,
        # 'Asset & Material Inputs'!I74
        nox_per_fuel=53.5,
    ),
    "Emergency response and rescue vessels (ERRV)": dict(
        # 'Asset & Material Inputs'!F75
        fuel_consumption=10.0,
        # 'Well Planning'!H23
        waiting_on_weather=5,
        # 'Well Planning'!F23
        duration=3.0,
        # 'Well Planning'!G23
        exposure=10,
        # 'Asset & Material Inputs'!G75
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!H75
        fuel_density=835,
        # 'Asset & Material Inputs'!I75
        nox_per_fuel=53.5,
    ),
}


# v20.12.22
HELICOPTERS = {
    'Sikorsky S-92': dict(
        # 'Well Planning'!O19
        roundtrip_minutes=90,
        # 'Well Planning'!P19
        roundtrip_count=8,
        # 'Asset & Materials Input'!F86
        fuel_consumption=641,
        # 'Well Planning'!Q19
        exposure=50,
        # 'Asset & Materials Input'!G86
        co2_per_fuel=3.15,
        # 'Asset & Materials Input'!H86
        fuel_density=800.0,
        # 'Asset & Materials Input'!I86
        nox_per_fuel=53.5,
    ),
    'Super Puma': dict(
        # 'Well Planning'!O20
        roundtrip_minutes=91,
        # 'Well Planning'!P20
        roundtrip_count=9,
        # 'Asset & Materials Input'!F87
        fuel_consumption=650,
        # 'Well Planning'!Q20
        exposure=100,
        # 'Asset & Materials Input'!G87
        co2_per_fuel=3.15,
        # 'Asset & Materials Input'!H87
        fuel_density=800.0,
        # 'Asset & Materials Input'!I87
        nox_per_fuel=53.5,
    ),
}

# v20.12.22
MATERIALS = {
    'STEEL': dict(
        # 'Well Planning'!N55
        quantity=12,
        # 'Well Planning'!I37
        co2_per_unit=7,
    ),
    'CEMENT': dict(
        # 'Well Planning'!O55
        quantity=10,
        # 'Well Planning'!I38
        co2_per_unit=16,
    ),
    'BULK': dict(
        # 'Well Planning'!P55
        quantity=21,
        # 'Well Planning'!I39
        co2_per_unit=7,
    ),
    'CHEMICALS': dict(
        # 'Well Planning'!Q55
        quantity=7,
        # 'Well Planning'!I40
        co2_per_unit=22,
    ),
}


# v20.12.22
# Based on Phase 2
@pytest.fixture
def step() -> WellPlannerPlannedStep:
    well_plan = WellPlannerFactory(
        # 'Well Planner'!C11
        co2_per_fuel=3.17,
        # 'Asset & Material Inputs'!D50
        baseline__boilers_fuel_consumption_summer=1.0,
        # 'Asset & Material Inputs'!E50
        baseline__boilers_fuel_consumption_winter=1.5,
        # 'Well Planning'!D11,
        fuel_density=835,
        # 'Well Planning'!F11
        nox_per_fuel=53.5,
    )
    step = WellPlannerPlannedStepFactory(
        well_planner=well_plan,
        season=AssetSeason.WINTER,
        external_energy_supply_enabled=True,
    )
    ExternalEnergySupplyFactory(
        asset=step.well_planner.asset,
        # 'Calculation'!D261
        capacity=4.0,
        # 'Calculation'!G261
        generator_efficiency_factor=3.881,
        # 'Asset & Material Inputs'!I97
        co2=0.055,
        # 'Asset & Material Inputs'!K97
        nox=0.000001,
    )
    BaselineInputFactory(
        baseline=step.well_planner.baseline,
        phase=step.phase,
        mode=step.mode,
        season=step.season,
        # 'Well Planning'!H55
        value=128.75,
    )

    first_initiative_input = EmissionReductionInitiativeInputFactory(
        phase=step.phase,
        mode=step.mode,
        # 'Calculation'!F180
        value=9.0,
    )
    second_initiative_input = EmissionReductionInitiativeInputFactory(
        phase=step.phase,
        mode=step.mode,
        # 'Calculation'!F188
        value=8.0,
    )
    step.emission_reduction_initiatives.add(
        first_initiative_input.emission_reduction_initiative, second_initiative_input.emission_reduction_initiative
    )

    for name, data in VESSELS.items():
        PlannedVesselUseFactory(
            well_planner=well_plan,
            season=AssetSeason.WINTER,
            duration=data['duration'],
            waiting_on_weather=data['waiting_on_weather'],
            exposure_against_current_well=data['exposure'],
            vessel_type__type=name,
            vessel_type__fuel_consumption_winter=data['fuel_consumption'],
            vessel_type__co2_per_fuel=data['co2_per_fuel'],
            vessel_type__fuel_density=data['fuel_density'],
            vessel_type__nox_per_fuel=data['nox_per_fuel'],
        )

    for name, data in HELICOPTERS.items():
        PlannedHelicopterUseFactory(
            well_planner=well_plan,
            trips=data['roundtrip_count'],
            trip_duration=data['roundtrip_minutes'],
            exposure_against_current_well=data['exposure'],
            helicopter_type__type=name,
            helicopter_type__fuel_consumption=data['fuel_consumption'],
            helicopter_type__co2_per_fuel=data['co2_per_fuel'],
            helicopter_type__fuel_density=data['fuel_density'],
            helicopter_type__nox_per_fuel=data['nox_per_fuel'],
        )

    for category, data in MATERIALS.items():
        WellPlannedStepMaterialFactory(
            step=step,
            quantity=data['quantity'],
            material_type__co2=data['co2_per_unit'],
            material_type__category=category,
        )

    return step


@pytest.mark.django_db
def test_calculate_planned_step_target_co2(step: WellPlannerPlannedStep):
    first_eri, second_eri = step.emission_reduction_initiatives.all().order_by('id')

    assert calculate_planned_step_target_co2(
        planned_step=step,
        # 'Calculation'!J247
        step_duration=6.132,
        # 'Calculation'!J255
        plan_duration=18.5766,
        season_duration=9.0216,
    ) == TargetCO2Data(
        # 'Calculation'!E25
        asset=1775.47795194,
        # 'Calculation'!J298
        boilers=29.15766,
        # 'Calculation'!I79
        vessels=730.7514106145252,
        # 'Calculation'!H130
        helicopters=13.224594505991407,
        # 'Calculation'!I159
        materials=545.0,
        # 'Calculation'!H272
        external_energy_supply=1.34904,
        emission_reduction_initiatives=[
            InitiativeReductionData(
                emission_reduction_initiative_id=first_eri.pk,
                # 'Calculation'!E9 multiplied by 'Well Planning'!C11
                value=225.2429235,
            ),
            InitiativeReductionData(
                emission_reduction_initiative_id=second_eri.pk,
                # 'Calculation'!E8 multiplied by 'Well Planning'!C11
                value=200.21593199999998,
            ),
        ],
    )


@pytest.mark.django_db
def test_calculate_planned_step_target_nox(step: WellPlannerPlannedStep):
    first_eri, second_eri = step.emission_reduction_initiatives.all().order_by('id')

    assert calculate_planned_step_target_nox(
        planned_step=step,
        # 'Calculation'!J247
        step_duration=6.132,
        # 'Calculation'!J255
        plan_duration=18.5766,
        season_duration=9.0216,
    ) == TargetNOXData(
        # 'Calculation'!E27 but based on 'Calculation'!E11
        asset=25.020516974145004,
        # 'Calculation'!K298
        boilers=0.03840165,
        # 'Calculation'!J79 but based on season duration and winter vessels
        vessels=10.297947126396648,
        # 'Calculation'!I113
        helicopters=0.1796865539226769,
        # 'Calculation'!J272
        external_energy_supply=0.000024527999999999996,
        emission_reduction_initiatives=[
            InitiativeReductionData(
                emission_reduction_initiative_id=first_eri.pk,
                # 'Calculation'!J180
                value=3.1741843848749998,
            ),
            InitiativeReductionData(
                emission_reduction_initiative_id=second_eri.pk,
                # 'Calculation'!J188
                value=2.8214972310000004,
            ),
        ],
    )
