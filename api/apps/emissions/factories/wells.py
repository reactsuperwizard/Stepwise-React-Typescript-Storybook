import factory.fuzzy
from django.utils import timezone

from apps.core.factories import CleanDjangoModelFactory
from apps.emissions.models import AssetSeason


class BaseWellStepMaterialFactory(CleanDjangoModelFactory):
    material_type = factory.SubFactory(
        "apps.emissions.factories.MaterialTypeFactory", tenant=factory.SelfAttribute("..step.well_planner.asset.tenant")
    )
    quantity = 0.0
    quota = False


class WellPlannedStepMaterialFactory(BaseWellStepMaterialFactory):
    step = factory.SubFactory("apps.wells.factories.WellPlannerPlannedStepFactory")

    class Meta:
        model = "emissions.WellPlannedStepMaterial"


class WellCompleteStepMaterialFactory(BaseWellStepMaterialFactory):
    step = factory.SubFactory("apps.wells.factories.WellPlannerCompleteStepFactory")

    class Meta:
        model = 'emissions.WellCompleteStepMaterial'


class WellNameFactory(CleanDjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    name = factory.Sequence(lambda n: f"Well name {n}")

    class Meta:
        model = 'emissions.WellName'
        django_get_or_create = (
            'tenant',
            'name',
        )


class BaseVesselUseFactory(CleanDjangoModelFactory):
    well_planner = factory.SubFactory('apps.wells.factories.WellPlannerFactory')
    vessel_type = factory.SubFactory('apps.emissions.factories.VesselTypeFactory')
    duration = factory.fuzzy.FuzzyFloat(2, 10)
    exposure_against_current_well = factory.fuzzy.FuzzyFloat(0, 100)
    waiting_on_weather = factory.fuzzy.FuzzyFloat(0, 100)
    season = AssetSeason.SUMMER
    quota_obligation = factory.fuzzy.FuzzyFloat(0, 100)


class PlannedVesselUseFactory(BaseVesselUseFactory):
    class Meta:
        model = 'emissions.PlannedVesselUse'


class CompleteVesselUseFactory(BaseVesselUseFactory):
    approved = False

    class Meta:
        model = 'emissions.CompleteVesselUse'


class BaseHelicopterUseFactory(CleanDjangoModelFactory):
    well_planner = factory.SubFactory('apps.wells.factories.WellPlannerFactory')
    helicopter_type = factory.SubFactory('apps.emissions.factories.HelicopterTypeFactory')
    trips = 14
    trip_duration = 60
    exposure_against_current_well = 50.5
    quota_obligation = 10.5


class PlannedHelicopterUseFactory(BaseHelicopterUseFactory):
    class Meta:
        model = 'emissions.PlannedHelicopterUse'


class CompleteHelicopterUseFactory(BaseHelicopterUseFactory):
    approved = False

    class Meta:
        model = 'emissions.CompleteHelicopterUse'


class BaseCO2Factory(CleanDjangoModelFactory):
    planned_step = factory.SubFactory('apps.wells.factories.WellPlannerPlannedStepFactory')
    datetime = timezone.now()
    asset = 2500.0
    boilers = 50.0
    vessels = 1000.0
    helicopters = 20.0
    materials = 300.0
    external_energy_supply = 2.0


class BaselineCO2Factory(BaseCO2Factory):
    class Meta:
        model = 'emissions.BaselineCO2'
        django_get_or_create = (
            'planned_step',
            'datetime',
        )


class TargetCO2Factory(BaseCO2Factory):
    class Meta:
        model = 'emissions.TargetCO2'
        django_get_or_create = (
            'planned_step',
            'datetime',
        )


class TargetCO2ReductionFactory(CleanDjangoModelFactory):
    target = factory.SubFactory('apps.emissions.factories.TargetCO2Factory')
    emission_reduction_initiative = factory.SubFactory('apps.emissions.factories.EmissionReductionInitiativeFactory')
    value = 20.0

    class Meta:
        model = 'emissions.TargetCO2Reduction'


class BaseNOXFactory(CleanDjangoModelFactory):
    planned_step = factory.SubFactory('apps.wells.factories.WellPlannerPlannedStepFactory')
    datetime = timezone.now()
    asset = 2500.0
    boilers = 50.0
    vessels = 1000.0
    helicopters = 20.0
    external_energy_supply = 2.0


class BaselineNOXFactory(BaseNOXFactory):
    class Meta:
        model = 'emissions.BaselineNOX'


class TargetNOXFactory(BaseNOXFactory):
    class Meta:
        model = 'emissions.TargetNOX'


class TargetNOXReductionFactory(CleanDjangoModelFactory):
    target = factory.SubFactory('apps.emissions.factories.TargetNOXFactory')
    emission_reduction_initiative = factory.SubFactory('apps.emissions.factories.EmissionReductionInitiativeFactory')
    value = 0.0

    class Meta:
        model = 'emissions.TargetNOXReduction'
