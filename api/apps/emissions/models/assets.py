from colorfield.fields import ColorField
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import DeletableModel, TimestampedModel
from apps.core.queryset import LiveQuerySet
from apps.tenants.models import TenantAwareModel

AssetManager = models.Manager.from_queryset(LiveQuerySet)


class AssetType(models.TextChoices):
    JACKUP = 'JACKUP', 'Jackup'
    SEMI = 'SEMI', 'Semi-submersible'
    DRILLSHIP = 'DRILLSHIP', 'Drillship'
    FIXED_PLATFORM = 'FIXED_PLATFORM', 'Fixed platform'


class Asset(TenantAwareModel, TimestampedModel, DeletableModel):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=16, choices=AssetType.choices)
    green_house_gas_class_notation = models.CharField(max_length=255, blank=True)
    design_description = models.TextField()
    vessel = models.OneToOneField('kims.Vessel', on_delete=models.PROTECT, null=True, blank=True)
    draft = models.BooleanField()

    objects = AssetManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(condition=models.Q(deleted=False), fields=["name"], name="unique_asset_name"),
        ]

    def __str__(self) -> str:
        return self.name


class AssetReferenceMaterial(TimestampedModel, DeletableModel):
    tenant = models.OneToOneField("tenants.Tenant", on_delete=models.PROTECT)
    details = models.URLField(blank=True, help_text='Asset details material')
    baseline = models.URLField(blank=True, help_text='Asset baseline material')
    emp = models.URLField(blank=True, help_text='Asset EMP material')

    def __str__(self):
        return f"Asset Reference Material: {self.pk}"


class ConceptPhase(TenantAwareModel, TimestampedModel):
    name = models.CharField(max_length=32)
    description = models.TextField()
    transit = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='unique_concept_phase_name'),
            models.UniqueConstraint(
                fields=['tenant', 'transit'], condition=models.Q(transit=True), name='unique_concept_phase_transit'
            ),
        ]

    def __str__(self):
        return self.name


class CustomPhase(TimestampedModel):
    phase = models.ForeignKey('emissions.ConceptPhase', on_delete=models.PROTECT, null=True, blank=True)
    asset = models.ForeignKey('emissions.Asset', on_delete=models.PROTECT)
    name = models.CharField(max_length=32)
    description = models.TextField()
    color = ColorField()

    class Meta:
        unique_together = ('asset', 'name')

    def __str__(self):
        return self.name

    @property
    def transit(self) -> bool:
        return self.phase.transit if self.phase else False


class ConceptMode(TenantAwareModel, TimestampedModel):
    name = models.CharField(max_length=32)
    description = models.TextField()
    asset_types = ArrayField(
        models.CharField(max_length=16, choices=AssetType.choices), help_text='Compatible asset types'
    )
    transit = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='unique_concept_mode_name'),
            models.UniqueConstraint(
                fields=['tenant', 'transit'], condition=models.Q(transit=True), name='unique_concept_mode_transit'
            ),
        ]

    def __str__(self):
        return self.name


class CustomMode(TimestampedModel):
    asset = models.ForeignKey('emissions.Asset', on_delete=models.PROTECT)
    mode = models.ForeignKey('emissions.ConceptMode', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=32)
    description = models.TextField()

    class Meta:
        unique_together = ('asset', 'name')

    def __str__(self):
        return self.name

    @property
    def transit(self) -> bool:
        return self.mode.transit if self.mode else False


class AbstractAssetInput(models.Model):
    phase = models.ForeignKey('emissions.CustomPhase', on_delete=models.PROTECT)
    mode = models.ForeignKey('emissions.CustomMode', on_delete=models.PROTECT)
    value = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        abstract = True


class AssetInputQuerySet(models.QuerySet):
    def inputs(self):
        return self.exclude(models.Q(phase__phase__transit=True) | models.Q(mode__mode__transit=True))

    def transit(self):
        return self.filter(phase__phase__transit=True, mode__mode__transit=True)


class BaselineQuerySet(LiveQuerySet):
    def live(self) -> "BaselineQuerySet":
        return self.filter(deleted=False, asset__deleted=False)


BaselineManager = models.Manager.from_queryset(BaselineQuerySet)


class Baseline(TimestampedModel, DeletableModel):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name='baselines')
    name = models.CharField(max_length=255)
    description = models.TextField()
    boilers_fuel_consumption_summer = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Boilers fuel consumption summer (m3 fuel/day)'
    )
    boilers_fuel_consumption_winter = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Boilers fuel consumption winter (m3 fuel/day)'
    )
    active = models.BooleanField()
    draft = models.BooleanField()

    objects = BaselineManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(active=True), fields=["asset", "active"], name="unique_active_baseline"
            ),
            models.CheckConstraint(
                check=models.Q(active=True, draft=False) | models.Q(active=False), name='active_baseline_never_draft'
            ),
            models.UniqueConstraint(
                condition=models.Q(deleted=False), fields=["asset", "name"], name="unique_baseline_name"
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def is_used(self) -> bool:
        return (
            self.wellplanner_set.live().exists()
            or EmissionReductionInitiative.objects.live().filter(emission_management_plan__baseline=self).exists()
        )


class AssetSeason(models.TextChoices):
    SUMMER = 'SUMMER', 'Summer'
    WINTER = 'WINTER', 'Winter'


BaselineInputManager = models.Manager.from_queryset(AssetInputQuerySet)


class BaselineInput(AbstractAssetInput):
    baseline = models.ForeignKey(Baseline, on_delete=models.PROTECT)
    season = models.CharField(choices=AssetSeason.choices, max_length=16)
    order = models.PositiveIntegerField()

    objects = BaselineInputManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'baseline',
                    'phase',
                    'mode',
                    'season',
                ],
                name='unique_baseline_input',
            ),
            models.UniqueConstraint(
                fields=[
                    'baseline',
                    'order',
                ],
                name='unique_baseline_input_order',
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]

    def __str__(self):
        return f"Baseline Input {self.pk}"


class EmissionManagementPlanQuerySet(LiveQuerySet):
    def live(self) -> "EmissionManagementPlanQuerySet":
        return self.filter(deleted=False, baseline__deleted=False, baseline__asset__deleted=False)


EmissionManagementPlanManager = models.Manager.from_queryset(EmissionManagementPlanQuerySet)


class EmissionManagementPlan(TimestampedModel, DeletableModel):
    baseline = models.ForeignKey(Baseline, on_delete=models.PROTECT, related_name='emission_management_plans')
    name = models.CharField(max_length=255)
    description = models.TextField()
    version = models.CharField(max_length=50)
    draft = models.BooleanField()
    active = models.BooleanField()

    objects = EmissionManagementPlanManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(active=True),
                fields=["baseline", "active"],
                name="unique_active_emission_management_plan",
            ),
            models.CheckConstraint(
                check=models.Q(active=True, draft=False) | models.Q(active=False),
                name='active_emission_management_plan_never_draft',
            ),
            models.CheckConstraint(
                check=models.Q(active=True, deleted=False) | models.Q(active=False),
                name='active_emission_management_plan_never_deleted',
            ),
        ]

    def __str__(self):
        return self.name


class EmissionReductionInitiativeType(models.TextChoices):
    POWER_SYSTEMS = 'POWER_SYSTEMS', 'Power systems'
    BASELOADS = 'BASELOADS', 'Baseloads'
    PRODUCTIVITY = 'PRODUCTIVITY', 'Productivity'


EmissionReductionInitiativeManager = models.Manager.from_queryset(LiveQuerySet)


class EmissionReductionInitiative(DeletableModel):
    emission_management_plan = models.ForeignKey(
        EmissionManagementPlan, on_delete=models.PROTECT, related_name='emission_reduction_initiatives'
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(choices=EmissionReductionInitiativeType.choices, max_length=20)
    vendor = models.CharField(max_length=100)
    deployment_date = models.DateField()

    objects = EmissionReductionInitiativeManager()

    def __str__(self):
        return self.name


EmissionReductionInitiativeInputManager = models.Manager.from_queryset(AssetInputQuerySet)


class EmissionReductionInitiativeInput(AbstractAssetInput):
    emission_reduction_initiative = models.ForeignKey(
        EmissionReductionInitiative, on_delete=models.CASCADE, related_name='emission_reduction_initiative_inputs'
    )

    objects = EmissionReductionInitiativeInputManager()

    class Meta:
        unique_together = [
            'emission_reduction_initiative',
            'phase',
            'mode',
        ]

    def __str__(self):
        return f"Emission Reduction Initiative Input: {self.pk}"


VesselTypeManager = models.Manager.from_queryset(LiveQuerySet)


class VesselType(TenantAwareModel, TimestampedModel, DeletableModel):
    type = models.CharField(max_length=255)
    fuel_type = models.CharField(max_length=255)
    fuel_density = models.FloatField(help_text='Fuel density (kg/m3)', validators=[MinValueValidator(0)])
    co2_per_fuel = models.FloatField(help_text='Ton CO2/m3 fuel', validators=[MinValueValidator(0)])
    nox_per_fuel = models.FloatField(help_text='Kg NOx/Ton Fuel', validators=[MinValueValidator(0)])
    co2_tax = models.FloatField(help_text='CO2 tax (USD/m3)', validators=[MinValueValidator(0)])
    nox_tax = models.FloatField(help_text='NOx tax (USD/m3)', validators=[MinValueValidator(0)])
    fuel_cost = models.FloatField(help_text='Fuel cost (USD/m3)', validators=[MinValueValidator(0)])
    fuel_consumption_summer = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Fuel consumption summer (m3/day)'
    )
    fuel_consumption_winter = models.FloatField(
        validators=[MinValueValidator(0)], help_text='Fuel consumption winter (m3/day)'
    )

    objects = VesselTypeManager()

    def __str__(self):
        return f"Vessel type: {self.type}"


HelicopterTypeManager = models.Manager.from_queryset(LiveQuerySet)


class HelicopterType(TenantAwareModel, TimestampedModel, DeletableModel):
    type = models.CharField(max_length=255)
    fuel_density = models.FloatField(validators=[MinValueValidator(0)], help_text="Fuel density (kg/m3)")
    co2_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text='Ton CO2/m3 fuel')
    nox_per_fuel = models.FloatField(validators=[MinValueValidator(0)], help_text="kg NOx/m3 fuel")
    fuel_consumption = models.FloatField(validators=[MinValueValidator(0)], help_text="Fuel consumption (Litres/h)")
    fuel_cost = models.FloatField(validators=[MinValueValidator(0)], help_text="Fuel cost (USD/m3)")
    co2_tax = models.FloatField(help_text='CO2 tax (USD/m3)', validators=[MinValueValidator(0)])
    nox_tax = models.FloatField(help_text='NOx tax (USD/m3)', validators=[MinValueValidator(0)])

    objects = HelicopterTypeManager()

    def __str__(self):
        return f"Helicopter type: {self.type}"


class MaterialCategory(models.TextChoices):
    STEEL = 'STEEL', 'Steel'
    CEMENT = 'CEMENT', 'Cement'
    BULK = 'BULK', 'Bulk'
    CHEMICALS = 'CHEMICALS', 'Chemicals'


MaterialTypeManager = models.Manager.from_queryset(LiveQuerySet)


class MaterialType(TenantAwareModel, TimestampedModel, DeletableModel):
    category = models.CharField(choices=MaterialCategory.choices, max_length=64)
    type = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    co2 = models.FloatField(validators=[MinValueValidator(0)], help_text="Ton CO2/unit")

    objects = MaterialTypeManager()

    def __str__(self):
        return f"Material type: {self.type}"


class ExternalEnergySupply(TimestampedModel):
    asset = models.OneToOneField('emissions.Asset', on_delete=models.PROTECT, related_name='external_energy_supply')
    type = models.CharField(max_length=255, help_text='External energy supply type')
    capacity = models.FloatField(validators=[MinValueValidator(0)], help_text='Capacity (MWh/day)')
    co2 = models.FloatField(validators=[MinValueValidator(0)], help_text="Ton CO2/MWh")
    nox = models.FloatField(validators=[MinValueValidator(0)], help_text="Kg NOx / MWh")
    generator_efficiency_factor = models.FloatField(
        validators=[MinValueValidator(0)], help_text="Generator efficiency factor (MWh/m3 fuel)"
    )

    class Meta:
        verbose_name = "External Energy Supply"
        verbose_name_plural = "External Energy Supplies"

    def __str__(self):
        return f"External energy supply: {self.pk}"
