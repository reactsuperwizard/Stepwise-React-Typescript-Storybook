import factory.fuzzy
from django.utils import timezone

from apps.core.factories import CleanDjangoModelFactory
from apps.emissions.models import AssetSeason
from apps.wells.models import (
    ConceptWell,
    CustomWell,
    SimpleMediumDemanding,
    WellPlannerWellType,
    WellPlannerWizardStep,
    WellType,
)


class BaseWellFactory(CleanDjangoModelFactory):
    type = WellType.EXPLORATION
    top_hole = SimpleMediumDemanding.SIMPLE
    transport_section = SimpleMediumDemanding.SIMPLE
    reservoir_section = SimpleMediumDemanding.SIMPLE
    completion = SimpleMediumDemanding.SIMPLE
    pna = SimpleMediumDemanding.SIMPLE
    season = ConceptWell.Season.YEARLY_AVERAGE
    metocean_data = ConceptWell.MetoceanData.GENERIC_NORWEGIAN_SEA
    metocean_days_above_hs_5 = 6.0
    water_depth = 0.0
    planned_time_per_well = 0.0
    tvd_from_msl = 0
    md_from_msl = 0
    expected_reservoir_pressure = 0
    expected_reservoir_temperature = 0.0
    top_hole_section_hole_size = 0.0
    surface_casing_section_hole_size = 0.0
    intermediate_casing_section_hole_size = 0.0
    production_casing_section_hole_size = 0.0
    extension_section_hole_size = 0.0
    intermediate_casing_section_mud_type = ConceptWell.MudType.OIL_BASED
    production_casing_section_mud_type = ConceptWell.MudType.OIL_BASED
    extension_section_mud_type = ConceptWell.MudType.OIL_BASED
    intermediate_casing_section_mud_density = 0.0
    production_casing_section_mud_density = 0.0
    extension_section_mud_density = 0.0
    conductor_size = 0.0
    conductor_weight = 0.0
    conductor_tvd_shoe_depth = 0.0
    conductor_md_shoe_depth = 0.0
    surface_casing_size = 0.0
    surface_casing_weight = 0.0
    surface_casing_tvd_shoe_depth = 0
    surface_casing_md_shoe_depth = 0
    intermediate_casing_size = 0.0
    intermediate_casing_weight = 0.0
    intermediate_casing_tvd_shoe_depth = 0
    intermediate_casing_md_shoe_depth = 0
    production_casing_size = 0.0
    production_casing_weight = 0.0
    production_casing_tvd_shoe_depth = 0
    production_casing_md_shoe_depth = 0
    liner_other_size = 0.0
    liner_other_weight = 0.0
    liner_other_tvd_shoe_depth = 0
    liner_other_md_shoe_depth = 0
    no_well_to_be_completed = 0
    planned_time_per_completion_operation = 0
    subsea_xmas_tree_size = 0.0
    xt_weight = 1.0
    lrp_size = 0.0
    lrp_weight = 0.0
    xt_running_tool_size = 0.0
    xt_running_tool_weight = 0.0

    @factory.post_generation
    def created_at(self, create, extracted, **kwargs):
        if create and extracted:
            self.created_at = extracted


class ConceptWellFactory(BaseWellFactory):
    name = factory.Sequence(lambda n: f"concept-well-{n}")

    class Meta:
        model = ConceptWell


class CustomWellFactory(BaseWellFactory):
    name = factory.Sequence(lambda n: f"custom-well-{n}")
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    creator = factory.SubFactory('apps.tenants.factories.UserFactory')
    project = factory.SubFactory("apps.projects.factories.ProjectFactory")
    draft = False

    class Meta:
        model = CustomWell


class WellPlannerFactory(CleanDjangoModelFactory):
    asset = factory.SubFactory("apps.emissions.factories.AssetFactory")
    name = factory.SubFactory(
        "apps.emissions.factories.WellNameFactory", tenant=factory.SelfAttribute('..asset.tenant')
    )
    baseline = factory.SubFactory("apps.emissions.factories.BaselineFactory", asset=factory.SelfAttribute('..asset'))
    emission_management_plan = factory.SubFactory(
        "apps.emissions.factories.EmissionManagementPlanFactory", baseline=factory.SelfAttribute('..baseline')
    )
    type = WellPlannerWellType.PRODUCTION
    location = factory.Sequence(lambda n: f"Location {n}")
    field = factory.Sequence(lambda n: f"Field {n}")
    current_step = WellPlannerWizardStep.WELL_PLANNING
    planned_start_date = timezone.now().date()
    actual_start_date = factory.LazyAttribute(
        lambda well_planner: None
        if well_planner.current_step == WellPlannerWizardStep.WELL_PLANNING
        else timezone.now().date()
    )
    fuel_type = "Marine diesel"
    fuel_density = 850.0
    co2_per_fuel = 3.17
    nox_per_fuel = 52.0
    co2_tax = 3.0
    nox_tax = 4.0
    fuel_cost = 800.0
    boilers_co2_per_fuel = 3.17
    boilers_nox_per_fuel = 5.0
    deleted = False

    class Meta:
        model = 'wells.WellPlanner'


class BaseWellPlannerStepFactory(CleanDjangoModelFactory):
    well_planner = factory.SubFactory(WellPlannerFactory)
    duration = 7.0
    phase = factory.SubFactory(
        'apps.emissions.factories.CustomPhaseFactory', asset=factory.SelfAttribute('..well_planner.asset')
    )
    mode = factory.SubFactory(
        'apps.emissions.factories.CustomModeFactory', asset=factory.SelfAttribute('..well_planner.asset')
    )
    season = AssetSeason.SUMMER
    well_section_length = 100.0
    waiting_on_weather = 100.0
    comment = factory.Sequence(lambda n: f"comment-{n}")
    carbon_capture_storage_system_quantity = None
    external_energy_supply_enabled = False
    external_energy_supply_quota = False


class WellPlannerPlannedStepFactory(BaseWellPlannerStepFactory):
    improved_duration = 5.0

    class Meta:
        model = 'wells.WellPlannerPlannedStep'


class WellPlannerCompleteStepFactory(BaseWellPlannerStepFactory):
    approved = False

    class Meta:
        model = 'wells.WellPlannerCompleteStep'


class WellReferenceMaterialFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    details = factory.Faker('url')
    vehicles = factory.Faker('url')
    planning = factory.Faker('url')
    complete = factory.Faker('url')

    class Meta:
        model = 'wells.WellReferenceMaterial'
        django_get_or_create = ('tenant',)
