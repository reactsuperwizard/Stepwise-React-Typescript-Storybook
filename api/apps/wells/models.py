from typing import cast

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Value
from ordered_model.models import OrderedModel

from apps.core.models import DeletableModel, TenantAwareModel, TimestampedModel
from apps.core.queryset import LiveQuerySet
from apps.core.validators import GreaterThanValidator
from apps.emissions.models import AssetSeason
from apps.projects.models import ElementType


class WellType(models.TextChoices):
    PRODUCTION = "PRODUCTION", "Production"
    EXPLORATION = "EXPLORATION", "Exploration"
    PNA = "PNA", "P&A"


class WellPlannerWizardStep(models.TextChoices):
    WELL_PLANNING = "WELL_PLANNING"
    WELL_REVIEWING = "WELL_REVIEWING"
    WELL_REPORTING = "WELL_REPORTING"


class SimpleMediumDemanding(models.TextChoices):
    SIMPLE = "SIMPLE", "Simple"
    MEDIUM = "MEDIUM", "Medium"
    DEMANDING = "DEMANDING", "Demanding"


def AbstractWellFactory(draft: bool) -> type[models.Model]:
    class AbstractWell(TimestampedModel):
        class Season(models.TextChoices):
            YEARLY_AVERAGE = "YEARLY_AVERAGE", "Yearly Average"
            SUMMER = "SUMMER", "Summer"
            WINTER = "WINTER", "Winter"
            SPECIFIC = "SPECIFIC", "Specific"

        class MudType(models.TextChoices):
            OIL_BASED = "OIL_BASED", "Oil based"
            WATER_BASED = "WATER_BASED", "Water based"

        class MetoceanData(models.TextChoices):
            GENERIC_NORTH_SEA = "GENERIC_NORTH_SEA", "Generic North Sea"
            GENERIC_NORWEGIAN_SEA = "GENERIC_NORWEGIAN_SEA", "Generic Norwegian Sea"
            GENERIC_BARENTS_SEA = "GENERIC_BARENTS_SEA", "Generic Barents Sea"
            CLIENT_SPECIFIC = "CLIENT_SPECIFIC", "Client specific"

        name = models.CharField(max_length=255, blank=draft)
        type = models.CharField(max_length=16, choices=WellType.choices, blank=draft)
        top_hole = models.CharField(
            max_length=16, choices=SimpleMediumDemanding.choices, verbose_name='Top hole 36" & 26"', blank=draft
        )
        transport_section = models.CharField(
            max_length=16,
            choices=SimpleMediumDemanding.choices,
            verbose_name='Transport section 17 1/2" & 12 1/4"',
            blank=draft,
        )
        reservoir_section = models.CharField(
            max_length=16, choices=SimpleMediumDemanding.choices, verbose_name='Reservoir section 8 1/2"', blank=draft
        )
        completion = models.CharField(
            max_length=16, choices=SimpleMediumDemanding.choices, verbose_name="Completion", blank=draft
        )
        pna = models.CharField(max_length=16, choices=SimpleMediumDemanding.choices, verbose_name="P&A", blank=draft)
        season = models.CharField(max_length=16, choices=Season.choices, verbose_name="Season", blank=draft)
        water_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(10000)],
            verbose_name="Water depth (ft)",
            null=draft,
            blank=draft,
        )
        metocean_data = models.CharField(
            max_length=30, choices=MetoceanData.choices, verbose_name='Metocean data', blank=draft
        )
        metocean_days_above_hs_5 = models.FloatField(
            verbose_name='Metocean days above HS 5',
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(30)],
        )
        tvd_from_msl = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='TVD from MSL (m)',
            null=draft,
            blank=draft,
        )
        # drilling data
        planned_time_per_well = models.FloatField(
            verbose_name='Planned time per well, d (time/depth curve)',
            null=True,
            blank=True,
            validators=[MinValueValidator(0), MaxValueValidator(365)],
        )
        md_from_msl = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='MD from MSL (m)',
            null=True,
            blank=True,
        )
        expected_reservoir_pressure = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(25000)],
            verbose_name='Expected reservoir pressure (bar)',
            null=True,
            blank=True,
        )
        expected_reservoir_temperature = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(200)],
            verbose_name='Expected reservoir temperature (C)',
            null=True,
            blank=True,
        )
        top_hole_section_hole_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Top hole section hole size (inch)',
            null=True,
            blank=True,
        )
        surface_casing_section_hole_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Surface casing section hole size (inch)',
            null=True,
            blank=True,
        )
        intermediate_casing_section_hole_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Intermediate casing section hole size (inch)',
            null=True,
            blank=True,
        )
        production_casing_section_hole_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Production casing section hole size (inch)',
            null=True,
            blank=True,
        )
        extension_section_hole_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Extension section hole size (inch)',
            null=True,
            blank=True,
        )
        intermediate_casing_section_mud_type = models.CharField(
            max_length=20, choices=MudType.choices, verbose_name='Intermediate casing section mud type', blank=True
        )
        production_casing_section_mud_type = models.CharField(
            max_length=20, choices=MudType.choices, verbose_name='Production casing section mud type', blank=True
        )
        extension_section_mud_type = models.CharField(
            max_length=20, choices=MudType.choices, verbose_name='Extension section mud type', blank=True
        )
        intermediate_casing_section_mud_density = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(15)],
            verbose_name='Intermediate casing section mud density (10-3kg/m3)',
            null=True,
            blank=True,
        )
        production_casing_section_mud_density = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(15)],
            verbose_name='Production casing section mud density (10-3kg/m3)',
            null=True,
            blank=True,
        )
        extension_section_mud_density = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(15)],
            verbose_name='Extension section mud density (10-3kg/m3)',
            null=True,
            blank=True,
        )
        conductor_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Conductor size (inch)',
            null=True,
            blank=True,
        )
        conductor_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Conductor weight (lbs/ft)',
            null=True,
            blank=True,
        )
        conductor_tvd_shoe_depth = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Conductor TVD shoe depth (m)',
            null=True,
            blank=True,
        )
        conductor_md_shoe_depth = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Conductor MD shoe depth (m)',
            null=True,
            blank=True,
        )
        surface_casing_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Surface casing size (inch)',
            null=True,
            blank=True,
        )
        surface_casing_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Surface casing weight (lbs/ft)',
            null=True,
            blank=True,
        )
        surface_casing_tvd_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(10000)],
            verbose_name='Surface casing TVD shoe depth (m)',
            null=True,
            blank=True,
        )
        surface_casing_md_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(10000)],
            verbose_name='Surface casing MD shoe depth (m)',
            null=True,
            blank=True,
        )
        intermediate_casing_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Intermediate casing size (inch)',
            null=True,
            blank=True,
        )
        intermediate_casing_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Intermediate casing weight (lbs/ft)',
            null=True,
            blank=True,
        )
        intermediate_casing_tvd_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Intermediate casing TVD shoe depth (m)',
            null=True,
            blank=True,
        )
        intermediate_casing_md_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Intermediate casing MD shoe depth (m)',
            null=True,
            blank=True,
        )
        production_casing_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Production casing size (inch)',
            null=True,
            blank=True,
        )
        production_casing_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Production casing weight (lbs/ft)',
            null=True,
            blank=True,
        )
        production_casing_tvd_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Production casing TVD shoe depth (m)',
            null=True,
            blank=True,
        )
        production_casing_md_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Production casing MD shoe depth (m)',
            null=True,
            blank=True,
        )
        liner_other_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100)],
            verbose_name='Liner/other size (inch)',
            null=True,
            blank=True,
        )
        liner_other_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(1000)],
            verbose_name='Liner/other weight (lbs/ft)',
            null=True,
            blank=True,
        )
        liner_other_tvd_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Liner/other TVD shoe depth (m)',
            null=True,
            blank=True,
        )
        liner_other_md_shoe_depth = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name='Liner/other MD shoe depth (m)',
            null=True,
            blank=True,
        )
        # completion data
        no_well_to_be_completed = models.PositiveIntegerField(
            verbose_name='No. well to be completed',
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(100)],
        )
        planned_time_per_completion_operation = models.FloatField(
            verbose_name='Planned time per completion operation (days)',
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(100)],
        )
        subsea_xmas_tree_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(500)],
            verbose_name='Sub-sea X-mas tree size (m3)',
            null=draft,
            blank=draft,
        )
        xt_weight = models.FloatField(
            validators=[MinValueValidator(1), MaxValueValidator(100)],
            verbose_name='XT weight (t)',
            null=draft,
            blank=draft,
        )
        lrp_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(500)],
            verbose_name='LRP size (m3)',
            null=draft,
            blank=draft,
        )
        lrp_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(200)],
            verbose_name='LRP weight (t)',
            null=draft,
            blank=draft,
        )
        xt_running_tool_size = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(500)],
            verbose_name='XT running tool, size (m3)',
            null=draft,
            blank=draft,
        )
        xt_running_tool_weight = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(200)],
            verbose_name='XT running tool weight (t)',
            null=draft,
            blank=draft,
        )

        class Meta:
            abstract = True

        def __str__(self):
            return self.name

    return AbstractWell


class ConceptWell(AbstractWellFactory(False)):  # type: ignore
    pass


class CustomWellQuerySet(models.QuerySet):
    def with_element_type(self):
        return cast('CustomWellQuerySet', self.annotate(element_type=Value(ElementType.WELL)))


class CustomWell(TenantAwareModel, AbstractWellFactory(True)):  # type: ignore
    project = models.ForeignKey(
        'projects.Project', null=True, blank=True, on_delete=models.CASCADE, related_name="wells"
    )
    creator = models.ForeignKey('tenants.User', on_delete=models.PROTECT)
    draft = models.BooleanField()

    objects = CustomWellQuerySet.as_manager()


class WellPlannerWellType(models.TextChoices):
    EXPLORATION = 'EXPLORATION', 'Exploration'
    PRODUCTION = 'PRODUCTION', 'Production'
    APPRAISAL = 'APPRAISAL', 'Appraisal'


WellPlannerManager = models.Manager.from_queryset(LiveQuerySet)


class WellPlanner(TimestampedModel, DeletableModel):
    asset = models.ForeignKey('emissions.Asset', on_delete=models.PROTECT)
    baseline = models.ForeignKey('emissions.Baseline', on_delete=models.PROTECT)
    emission_management_plan = models.ForeignKey(
        'emissions.EmissionManagementPlan', blank=True, null=True, on_delete=models.PROTECT
    )
    name = models.ForeignKey('emissions.WellName', on_delete=models.PROTECT)
    sidetrack = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=WellPlannerWellType.choices)
    location = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    planned_start_date = models.DateField()
    actual_start_date = models.DateField(blank=True, null=True)
    fuel_type = models.CharField(max_length=255, help_text='Asset fuel type')
    fuel_density = models.FloatField(validators=[MinValueValidator(0)], help_text='Fuel density (kg/m3)')
    co2_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text='Ton CO2/m3 fuel')
    nox_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text='Kg NOx/Ton fuel')
    co2_tax = models.FloatField(validators=[MinValueValidator(0)], help_text="CO2 tax (USD/m3)")
    nox_tax = models.FloatField(validators=[MinValueValidator(0)], help_text="NOx tax (USD/m3)")
    fuel_cost = models.FloatField(validators=[MinValueValidator(0)], help_text="Fuel cost (USD/m3)")
    boilers_co2_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text='Ton CO2/m3 fuel for boilers')
    boilers_nox_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text='Kg NOx/Ton fuel for boilers')

    current_step = models.CharField(choices=WellPlannerWizardStep.choices, max_length=32)

    objects = WellPlannerManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted=False),
                fields=["name", "sidetrack"],
                name="unique_well_planner_name_and_sidetrack",
            ),
        ]

    def __str__(self):
        return f'{self.name} {self.sidetrack}'


class BaseWellPlannerStep(TimestampedModel, OrderedModel):
    duration = models.FloatField(validators=[GreaterThanValidator(0)], help_text='Phase duration in days')
    phase = models.ForeignKey("emissions.CustomPhase", on_delete=models.CASCADE)
    mode = models.ForeignKey("emissions.CustomMode", on_delete=models.CASCADE)

    season = models.CharField(choices=AssetSeason.choices, max_length=16)
    emission_reduction_initiatives = models.ManyToManyField(
        'emissions.EmissionReductionInitiative',
        blank=True,
    )
    well_section_length = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Well section length in meters'
    )
    waiting_on_weather = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text='Waiting on weather contingency for selected days in percentage',
    )
    comment = models.TextField(blank=True)
    carbon_capture_storage_system_quantity = models.FloatField(
        validators=[MinValueValidator(0)], help_text='CC&S quantity in Tons of CO2 per day', blank=True, null=True
    )
    external_energy_supply_enabled = models.BooleanField()
    external_energy_supply_quota = models.BooleanField()

    order_with_respect_to = 'well_planner'

    class Meta:
        abstract = True


class WellPlannerPlannedStep(BaseWellPlannerStep):
    well_planner = models.ForeignKey('wells.WellPlanner', on_delete=models.CASCADE, related_name='planned_steps')
    material_types = models.ManyToManyField(
        'emissions.MaterialType', through='emissions.WellPlannedStepMaterial', related_name='planned_steps'
    )

    improved_duration = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Phase improved duration in days'
    )

    @property
    def total_duration(self) -> float:
        return self.duration + self.waiting_on_weather / 100 * self.duration

    def __str__(self):
        return f"Well planner planned step: {self.pk}"

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(duration__gt=0), name="well_planner_planned_step__duration__gt_0"),
            models.CheckConstraint(
                check=Q(improved_duration__gt=0), name="well_planner_planned_step_improved__duration_gt_0"
            ),
        ]


WellPlannerPlannedStepEmissionReductionInitiativeRelation = (
    WellPlannerPlannedStep.emission_reduction_initiatives.through
)


class WellPlannerCompleteStep(BaseWellPlannerStep):
    well_planner = models.ForeignKey('wells.WellPlanner', on_delete=models.CASCADE, related_name='complete_steps')
    material_types = models.ManyToManyField(
        'emissions.MaterialType', through='emissions.WellCompleteStepMaterial', related_name='complete_steps'
    )

    approved = models.BooleanField()

    def __str__(self):
        return f"Well planner complete step: {self.pk}"

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(duration__gt=0), name="well_planner_complete_step__duration__gt_0"),
        ]


class WellReferenceMaterial(TimestampedModel):
    tenant = models.OneToOneField("tenants.Tenant", on_delete=models.PROTECT)
    details = models.URLField(blank=True, help_text='Well details material')
    vehicles = models.URLField(blank=True, help_text='Vessels & helicopters material')
    planning = models.URLField(blank=True, help_text='Well planning material')
    complete = models.URLField(blank=True, help_text='Well complete material')

    def __str__(self):
        return f"Well reference material: {self.pk}"
