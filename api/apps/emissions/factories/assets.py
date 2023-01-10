import datetime

import factory.fuzzy

from apps.core.factories import CleanDjangoModelFactory
from apps.emissions.models import AssetSeason, AssetType, EmissionReductionInitiativeType, MaterialCategory


class AssetFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    name = factory.Sequence(lambda n: f"asset-{n}")
    type = AssetType.JACKUP
    design_description = factory.Sequence(lambda n: f"asset-design-description-{n}")
    vessel = factory.SubFactory('apps.kims.factories.VesselFactory')
    draft = factory.Faker('pybool')

    class Meta:
        model = 'emissions.Asset'


class AssetReferenceMaterialFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    details = factory.Faker('url')
    baseline = factory.Faker('url')
    emp = factory.Faker('url')

    class Meta:
        model = 'emissions.AssetReferenceMaterial'
        django_get_or_create = ('tenant',)


class BaselineFactory(CleanDjangoModelFactory):
    asset = factory.SubFactory(AssetFactory)
    name = factory.Sequence(lambda n: f"Baseline {n}")
    description = factory.Sequence(lambda n: f"Baseline {n} description")
    boilers_fuel_consumption_summer = 30
    boilers_fuel_consumption_winter = 27.5
    active = False
    draft = factory.LazyAttribute(lambda baseline: not baseline.active)

    class Meta:
        model = 'emissions.Baseline'


class BaselineInputFactory(CleanDjangoModelFactory):
    baseline = factory.SubFactory(BaselineFactory)
    phase = factory.SubFactory(
        'apps.emissions.factories.CustomPhaseFactory', asset=factory.SelfAttribute('..baseline.asset')
    )
    mode = factory.SubFactory(
        'apps.emissions.factories.CustomModeFactory', asset=factory.SelfAttribute('..baseline.asset')
    )
    season = AssetSeason.SUMMER
    value = 0.0
    order = factory.LazyAttribute(lambda baseline_input: baseline_input.baseline.baselineinput_set.count())

    class Meta:
        model = 'emissions.BaselineInput'


class EmissionManagementPlanFactory(CleanDjangoModelFactory):
    baseline = factory.SubFactory(BaselineFactory)
    name = factory.Sequence(lambda n: f"Energy Management Plan {n}")
    description = factory.Sequence(lambda n: f"Energy Management Plan {n} description")
    version = factory.Sequence(lambda n: f'v{n}')
    active = False
    draft = factory.LazyAttribute(lambda emission_management_plan: not emission_management_plan.active)
    deleted = False

    class Meta:
        model = 'emissions.EmissionManagementPlan'


class EmissionReductionInitiativeFactory(CleanDjangoModelFactory):
    emission_management_plan = factory.SubFactory(EmissionManagementPlanFactory)
    name = factory.Sequence(lambda n: f"Energy Reduction Initiative {n}")
    description = factory.Sequence(lambda n: f"Energy Reduction Initiative {n} description")
    type = EmissionReductionInitiativeType.BASELOADS
    vendor = factory.Faker("company")
    deployment_date = datetime.date(2021, 6, 1)
    deleted = False

    class Meta:
        model = 'emissions.EmissionReductionInitiative'


class EmissionReductionInitiativeInputFactory(CleanDjangoModelFactory):
    emission_reduction_initiative = factory.SubFactory(EmissionReductionInitiativeFactory)
    phase = factory.SubFactory(
        'apps.emissions.factories.CustomPhaseFactory',
        asset=factory.SelfAttribute('..emission_reduction_initiative.emission_management_plan.baseline.asset'),
    )
    mode = factory.SubFactory(
        'apps.emissions.factories.CustomModeFactory',
        asset=factory.SelfAttribute('..emission_reduction_initiative.emission_management_plan.baseline.asset'),
    )
    value = 0.0

    class Meta:
        model = 'emissions.EmissionReductionInitiativeInput'


class ConceptPhaseFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    name = factory.Sequence(lambda n: f"concept-well-planner-phase-{n}")
    description = factory.Sequence(lambda n: f"concept-well-planner-phase-description-{n}")
    transit = False

    class Meta:
        model = 'emissions.ConceptPhase'


class CustomPhaseFactory(CleanDjangoModelFactory):
    phase = factory.SubFactory(
        ConceptPhaseFactory,
        tenant=factory.SelfAttribute('..asset.tenant'),
    )
    asset = factory.SubFactory(AssetFactory)
    name = factory.Sequence(lambda n: f"well-planner-phase-{n}")
    description = factory.Sequence(lambda n: f"concept-well-planner-mode-description-{n}")

    class Meta:
        model = 'emissions.CustomPhase'


class ConceptModeFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    name = factory.Sequence(lambda n: f"concept-well-planner-mode-{n}")
    description = factory.Sequence(lambda n: f"concept-well-planner-mode-description-{n}")
    asset_types = [AssetType.FIXED_PLATFORM, AssetType.SEMI, AssetType.JACKUP, AssetType.FIXED_PLATFORM]
    transit = False

    class Meta:
        model = 'emissions.ConceptMode'


class CustomModeFactory(CleanDjangoModelFactory):
    asset = factory.SubFactory("apps.emissions.factories.AssetFactory")
    mode = factory.SubFactory(
        "apps.emissions.factories.ConceptModeFactory",
        tenant=factory.SelfAttribute('..asset.tenant'),
    )
    name = factory.Sequence(lambda n: f"well-planner-mode-{n}")
    description = factory.Sequence(lambda n: f"concept-well-planner-mode-description-{n}")

    class Meta:
        model = 'emissions.CustomMode'


class VesselTypeFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    type = factory.Sequence(lambda n: f"Vessel Type {n}")
    fuel_type = 'fuel'
    fuel_density = 1.0
    co2_per_fuel = 2.0
    nox_per_fuel = 3.0
    co2_tax = 4.0
    nox_tax = 5.0
    fuel_cost = 6.0
    fuel_consumption_summer = 7.0
    fuel_consumption_winter = 8.0
    deleted = False

    class Meta:
        model = 'emissions.VesselType'


class HelicopterTypeFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    type = factory.Sequence(lambda n: f"Helicopter Type {n}")
    fuel_density = 1.0
    co2_per_fuel = 2.0
    nox_per_fuel = 3.0
    fuel_consumption = 4.0
    fuel_cost = 5.0
    co2_tax = 6.0
    nox_tax = 7.0
    deleted = False

    class Meta:
        model = 'emissions.HelicopterType'


class MaterialTypeFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    category = MaterialCategory.STEEL
    type = factory.Sequence(lambda n: f"Material Type {n}")
    unit = factory.Sequence(lambda n: f"Material Unit {n}")
    co2 = 0.0

    class Meta:
        model = 'emissions.MaterialType'


class ExternalEnergySupplyFactory(CleanDjangoModelFactory):
    asset = factory.SubFactory('apps.emissions.factories.AssetFactory')
    type = factory.Sequence(lambda n: f"External Energy Supply: {n}")
    capacity = 1.0
    co2 = 2.0
    nox = 3.0
    generator_efficiency_factor = 4.0

    class Meta:
        model = 'emissions.ExternalEnergySupply'
        django_get_or_create = ('asset',)
