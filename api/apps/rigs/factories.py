from datetime import datetime

import factory.fuzzy

from apps.core.factories import CleanDjangoModelFactory
from apps.rigs.models import Airgap, DPClass, HighMediumLow, RigStatus, TopsideDesign


class BaseRigFactory(CleanDjangoModelFactory):
    manager = factory.Sequence(lambda n: f"concept-rig-manager-{n}")
    design = factory.Sequence(lambda n: f"concept-rig-design-{n}")
    build_yard = factory.Sequence(lambda n: f"concept-rig-build-yard-{n}")
    rig_status = RigStatus.DRILLING
    delivery_date = factory.fuzzy.FuzzyDate(
        datetime(year=2022, month=1, day=1),
        datetime(year=2025, month=12, day=31),
    )
    special_survey_due = factory.fuzzy.FuzzyDate(
        datetime(year=2022, month=1, day=1),
        datetime(year=2027, month=12, day=31),
    )
    end_of_last_contract = factory.fuzzy.FuzzyDate(
        datetime(year=1970, month=1, day=1),
        datetime(year=2035, month=12, day=31),
    )
    months_in_operation_last_year = 0
    months_in_operation_last_3_years = 0
    design_score = HighMediumLow.LOW
    topside_design = TopsideDesign.NOV
    quarters_capacity = 10
    rig_water_depth = 0
    variable_load = 0
    hull_breadth = 100
    hull_depth = 10
    hull_length = 100
    derrick_height = 50
    derrick_capacity = 500000
    drawworks_power = 1000
    total_cranes = 1
    crane_capacity = 10
    total_bop_rams = 1
    bop_diameter_wp_max = 10
    bop_wp_max = 5000
    number_of_bop_stacks = 1
    mudpump_quantity = 1
    liquid_mud = 1000
    mud_total_power = 1000
    shaleshaker_total = 0
    engine_power = 0
    engine_quantity = 0
    engine_total = 0
    generator_power = 0
    generator_quantity = 0
    generator_total = 0
    offline_stand_building = False
    auto_pipe_handling = False
    dual_activity = False
    drilltronic = False
    dynamic_drilling_guide = False
    process_automation_platform = False
    automatic_tripping = False
    closed_bus = False
    scr = False
    hybrid = False
    hvac_heat_recovery = False
    freshwater_cooling_systems = False
    seawater_cooling_systems = False
    operator_awareness_dashboard = False
    hpu_optimization = False
    optimized_heat_tracing_system = False
    floodlighting_optimization = False
    vfds_on_aux_machinery = False
    day_rate = 300000
    spread_cost = 100000
    tugs_no_used = 3

    @factory.post_generation
    def created_at(self, create, extracted, **kwargs):
        if create and extracted:
            self.created_at = extracted


class BaseSemiRigFactory(BaseRigFactory):
    equipment_load = HighMediumLow.LOW
    drillfloor_efficiency = HighMediumLow.LOW
    hull_concept_score = 0
    hull_design_eco_score = 0
    dp = False
    dp_class = DPClass.DP2
    thruster_assist = False
    total_anchors = 0
    anchor_standalone = False
    airgap = Airgap.S
    draft_depth = 50
    displacement = 5000
    dual_derrick = False
    active_heave_drawwork = False
    cmc_with_active_heave = False
    ram_system = False
    tripsaver = False
    move_speed = 6


class BaseJackupRigFactory(BaseRigFactory):
    cantilever_reach = 0
    cantilever_lateral = 0
    cantilever_capacity = 1000000
    leg_length = 100
    leg_spacing = 100
    subsea_drilling = False
    enhanced_legs = False
    jack_up_time = 1.4
    jack_down_time = 1.6


class ConceptSemiRigFactory(BaseSemiRigFactory):
    name = factory.Sequence(lambda n: f"concept-semi-rig-{n}")

    class Meta:
        model = "rigs.ConceptSemiRig"


class ConceptJackupRigFactory(BaseJackupRigFactory):
    name = factory.Sequence(lambda n: f"concept-jackup-rig-{n}")

    class Meta:
        model = "rigs.ConceptJackupRig"


class BaseCustomRigFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    creator = factory.SubFactory('apps.tenants.factories.UserFactory')
    project = factory.SubFactory('apps.projects.factories.ProjectFactory')
    emp = factory.SubFactory('apps.emps.factories.EMPFactory')
    draft = False


class CustomSemiRigFactory(BaseCustomRigFactory, BaseSemiRigFactory):
    name = factory.Sequence(lambda n: f"custom-semi-rig-{n}")

    class Meta:
        model = "rigs.CustomSemiRig"


class CustomJackupRigFactory(BaseCustomRigFactory, BaseJackupRigFactory):
    name = factory.Sequence(lambda n: f"custom-jackup-rig-{n}")

    class Meta:
        model = "rigs.CustomJackupRig"


class BaseRigSubareaScoreFactory(factory.django.DjangoModelFactory):
    rig_status = factory.fuzzy.FuzzyFloat(0, 1)
    topside_efficiency = factory.fuzzy.FuzzyFloat(0, 1)
    deck_efficiency = factory.fuzzy.FuzzyFloat(0, 1)
    capacities = factory.fuzzy.FuzzyFloat(0, 1)
    co2 = factory.fuzzy.FuzzyFloat(0, 1)


class CustomJackupSubareaScoreFactory(BaseRigSubareaScoreFactory):
    rig = factory.SubFactory(CustomJackupRigFactory)
    move_and_installation = factory.fuzzy.FuzzyFloat(0, 1)

    class Meta:
        model = "rigs.CustomJackupSubareaScore"


class CustomSemiSubareaScoreFactory(BaseRigSubareaScoreFactory):
    rig = factory.SubFactory(CustomSemiRigFactory)
    wow = factory.fuzzy.FuzzyFloat(0, 1)

    class Meta:
        model = "rigs.CustomSemiSubareaScore"


class BaseRigPlanCO2Factory(factory.django.DjangoModelFactory):
    plan = factory.SubFactory("apps.projects.factories.PlanFactory")

    helicopter_trips = factory.fuzzy.FuzzyFloat(3000, 4000)
    helicopter_fuel = factory.fuzzy.FuzzyFloat(3000, 4000)
    helicopter_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    helicopter_co2 = factory.fuzzy.FuzzyFloat(3000, 4000)
    psv_trips = factory.fuzzy.FuzzyFloat(3000, 4000)
    psv_fuel = factory.fuzzy.FuzzyFloat(3000, 4000)
    psv_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    psv_co2 = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_fuel = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_co2 = factory.fuzzy.FuzzyFloat(3000, 4000)
    cost_per_meter = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_days = factory.fuzzy.FuzzyFloat(30, 90)


class CustomJackupPlanCO2Factory(BaseRigPlanCO2Factory):
    rig = factory.SubFactory(CustomJackupRigFactory)
    tugs_cost = factory.fuzzy.FuzzyFloat(3000, 4000)

    class Meta:
        model = "rigs.CustomJackupPlanCO2"


class CustomSemiPlanCO2Factory(BaseRigPlanCO2Factory):
    rig = factory.SubFactory(CustomSemiRigFactory)

    ahv_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_logistic_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_move_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_fuel_cost = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_transit_co2 = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_support_co2 = factory.fuzzy.FuzzyFloat(3000, 4000)
    total_rig_and_spread_cost = factory.fuzzy.FuzzyFloat(3000, 4000)

    class Meta:
        model = "rigs.CustomSemiPlanCO2"


class BaseDrillshipFactory(BaseRigFactory):
    equipment_load = HighMediumLow.LOW
    drillfloor_efficiency = HighMediumLow.HIGH
    rig_water_depth = 20000
    variable_load = 50000
    hull_concept_score = 10
    hull_design_eco_score = 10
    dp = True
    dp_class = DPClass.DP2
    draft_depth = 150
    displacement = 300000
    riser_on_board_outfitted = 20000
    riser_storage_inside_hull = True
    split_funnels_free_stern_deck = True
    dual_derrick = True
    active_heave_drawwork = True
    cmc_with_active_heave = True
    ram_system = True
    tripsaver = True


class ConceptDrillshipFactory(BaseDrillshipFactory):
    name = factory.Sequence(lambda n: f"concept-drillship-{n}")

    class Meta:
        model = "rigs.ConceptDrillship"


class CustomDrillshipFactory(BaseCustomRigFactory, BaseDrillshipFactory):
    name = factory.Sequence(lambda n: f"custom-drillship-{n}")

    class Meta:
        model = "rigs.CustomDrillship"


AnyCustomRigFactory = CustomJackupRigFactory | CustomSemiRigFactory | CustomDrillshipFactory
