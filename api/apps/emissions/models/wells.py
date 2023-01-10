from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TenantAwareModel, TimestampedModel
from apps.core.validators import GreaterThanValidator
from apps.emissions.models import AssetSeason


class WellName(TenantAwareModel):
    name = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="unique_well_name"),
        ]

    def __str__(self) -> str:
        return f'{self.tenant.name}: {self.name}'


class BaseVesselUse(TimestampedModel):
    well_planner = models.ForeignKey('wells.WellPlanner', on_delete=models.PROTECT)
    vessel_type = models.ForeignKey('emissions.VesselType', on_delete=models.PROTECT)
    duration = models.FloatField(validators=[GreaterThanValidator(0)], help_text='Duration (days)')
    exposure_against_current_well = models.FloatField(
        help_text='Percentage exposure against current well', validators=[MinValueValidator(0)]
    )
    waiting_on_weather = models.FloatField(
        help_text='Waiting on weather contingency (%)', validators=[MinValueValidator(0)]
    )
    season = models.CharField(choices=AssetSeason.choices, max_length=16)
    quota_obligation = models.FloatField(validators=[MinValueValidator(0)], help_text='Percentage quota obligation')

    class Meta:
        abstract = True

    @property
    def fuel_consumption(self) -> float:
        match self.season:
            case AssetSeason.WINTER:
                return self.vessel_type.fuel_consumption_winter
            case AssetSeason.SUMMER:
                return self.vessel_type.fuel_consumption_summer
            case _:
                raise ValueError(f'Unknown season: {self.season}')


class PlannedVesselUse(BaseVesselUse):
    @property
    def total_days(self) -> float:
        return self.duration + self.duration * (self.waiting_on_weather / 100)

    def __str__(self):
        return f"Planned vessel use: {self.pk}"


class CompleteVesselUse(BaseVesselUse):
    approved = models.BooleanField()

    def __str__(self):
        return f"Complete vessel use: {self.pk}"


class BaseWellStepMaterial(models.Model):
    material_type = models.ForeignKey('emissions.MaterialType', on_delete=models.PROTECT)
    quantity = models.FloatField(validators=[MinValueValidator(0)])
    quota = models.BooleanField()

    class Meta:
        abstract = True


class WellPlannedStepMaterial(BaseWellStepMaterial):
    step = models.ForeignKey('wells.WellPlannerPlannedStep', on_delete=models.CASCADE, related_name='materials')

    def __str__(self):
        return f"Well planned step material: {self.pk}"


class WellCompleteStepMaterial(BaseWellStepMaterial):
    step = models.ForeignKey('wells.WellPlannerCompleteStep', on_delete=models.CASCADE, related_name='materials')

    def __str__(self):
        return f"Well complete step material: {self.pk}"


class BaseHelicopterUse(TimestampedModel):
    well_planner = models.ForeignKey('wells.WellPlanner', on_delete=models.CASCADE)
    helicopter_type = models.ForeignKey('emissions.HelicopterType', on_delete=models.PROTECT)
    trips = models.IntegerField(validators=[MinValueValidator(1)], help_text="Number of round trips")
    trip_duration = models.IntegerField(
        validators=[GreaterThanValidator(0)], help_text="Flight time per round trip (minutes)"
    )
    exposure_against_current_well = models.FloatField(
        help_text='Percentage exposure against current well', validators=[MinValueValidator(0)]
    )
    quota_obligation = models.FloatField(validators=[MinValueValidator(0)], help_text='Percentage quota obligation')

    class Meta:
        abstract = True


class PlannedHelicopterUse(BaseHelicopterUse):
    def __str__(self):
        return f"Planned helicopter use: {self.pk}"


class CompleteHelicopterUse(BaseHelicopterUse):
    approved = models.BooleanField()

    def __str__(self):
        return f"Complete helicopter use: {self.pk}"


class BaseCO2(models.Model):
    planned_step = models.ForeignKey('wells.WellPlannerPlannedStep', on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    asset = models.FloatField(validators=[MinValueValidator(0)])
    boilers = models.FloatField(validators=[MinValueValidator(0)])
    vessels = models.FloatField(validators=[MinValueValidator(0)])
    helicopters = models.FloatField(validators=[MinValueValidator(0)])
    materials = models.FloatField(validators=[MinValueValidator(0)])
    external_energy_supply = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        abstract = True
        unique_together = ('planned_step', 'datetime')


class BaselineCO2(BaseCO2):
    class Meta(BaseCO2.Meta):
        verbose_name = 'Baseline CO2'

    def __str__(self):
        return f"Baseline CO2: {self.pk}"


class TargetCO2(BaseCO2):
    emission_reduction_initiatives = models.ManyToManyField(
        'emissions.EmissionReductionInitiative', through='emissions.TargetCO2Reduction'
    )

    class Meta(BaseCO2.Meta):
        verbose_name = 'Target CO2'

    def __str__(self):
        return f"Target CO2: {self.pk}"


class TargetCO2Reduction(models.Model):
    target = models.ForeignKey('emissions.TargetCO2', on_delete=models.CASCADE)
    emission_reduction_initiative = models.ForeignKey('emissions.EmissionReductionInitiative', on_delete=models.PROTECT)
    value = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Target CO2 reduction'
        unique_together = ('target', 'emission_reduction_initiative')

    def __str__(self):
        return f"Target CO2 reduction: {self.pk}"


class BaseNOX(models.Model):
    planned_step = models.ForeignKey('wells.WellPlannerPlannedStep', on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    asset = models.FloatField(validators=[MinValueValidator(0)])
    boilers = models.FloatField(validators=[MinValueValidator(0)])
    vessels = models.FloatField(validators=[MinValueValidator(0)])
    helicopters = models.FloatField(validators=[MinValueValidator(0)])
    external_energy_supply = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        abstract = True
        unique_together = ('planned_step', 'datetime')


class BaselineNOX(BaseNOX):
    class Meta(BaseNOX.Meta):
        verbose_name = 'Baseline NOX'

    def __str__(self):
        return f"Baseline NOX: {self.pk}"


class TargetNOX(BaseNOX):
    emission_reduction_initiatives = models.ManyToManyField(
        'emissions.EmissionReductionInitiative', through='emissions.TargetNOXReduction'
    )

    class Meta(BaseNOX.Meta):
        verbose_name = 'Target NOX'

    def __str__(self):
        return f"Target NOX: {self.pk}"


class TargetNOXReduction(models.Model):
    target = models.ForeignKey('emissions.TargetNOX', on_delete=models.CASCADE)
    emission_reduction_initiative = models.ForeignKey('emissions.EmissionReductionInitiative', on_delete=models.PROTECT)
    value = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Target NOX reduction'
        unique_together = ('target', 'emission_reduction_initiative')

    def __str__(self):
        return f"Target NOX reduction: {self.pk}"
