from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TenantAwareModel, TimestampedModel
from apps.core.validators import GreaterThanValidator


class Project(TimestampedModel, TenantAwareModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tugs_day_rate = models.FloatField(help_text="Tugs day rate (USD)", validators=[MinValueValidator(0)])
    tugs_avg_move_fuel_consumption = models.FloatField(
        help_text="Average Tug move fuel consumption (t/d)", validators=[MinValueValidator(0.1), MaxValueValidator(30)]
    )
    tugs_avg_transit_fuel_consumption = models.FloatField(
        help_text="Average Tug transit fuel consumption (t/d)",
        validators=[MinValueValidator(0.1), MaxValueValidator(30)],
    )
    tugs_move_speed = models.FloatField(
        help_text="Tug move speed (kn)", validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    tugs_transit_speed = models.FloatField(
        help_text="Tug transit speed (kn)", validators=[MinValueValidator(1), MaxValueValidator(40)]
    )
    ahv_no_used = models.PositiveIntegerField(
        help_text='Number of AHVs to be used', validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    ahv_no_days_per_location = models.FloatField(
        help_text="Number of AHV days per location", validators=[MinValueValidator(0)]
    )
    ahv_avg_fuel_consumption = models.FloatField(
        help_text="Average AHV fuel consumption (t/d)", validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    ahv_day_rate = models.FloatField(
        help_text="AHV day rate (USD)", validators=[MinValueValidator(0), MaxValueValidator(1000000)]
    )
    psv_calls_per_week = models.FloatField(
        help_text="PSV calls per week", validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    psv_types = models.TextField(help_text="Type of PSV's / names")
    psv_avg_fuel_transit_consumption = models.FloatField(
        help_text='Average PSV fuel transit consumption (t/d)',
        validators=[MinValueValidator(0.1), MaxValueValidator(50)],
    )
    psv_avg_fuel_dp_consumption = models.FloatField(
        help_text='Average PSV fuel DP consumption (t/d)', validators=[MinValueValidator(0.1), MaxValueValidator(30)]
    )
    psv_day_rate = models.FloatField(
        help_text='PSV day rate (USD)', validators=[MinValueValidator(0), MaxValueValidator(1000000)]
    )
    psv_speed = models.FloatField(help_text='PSV speed (kn)', validators=[MinValueValidator(1), MaxValueValidator(40)])
    psv_loading_time = models.FloatField(
        help_text='PSV loading time (d)', validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    psv_fuel_price = models.PositiveIntegerField(
        help_text='PSV fuel price (USD/t)', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    helicopter_no_flights_per_week = models.FloatField(
        help_text='Helicopter number of flights per week', validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    helicopter_types = models.TextField(help_text='Type of helicopters')
    helicopter_avg_fuel_consumption = models.FloatField(
        help_text='Helicopter average fuel consumption (t/d)', validators=[MinValueValidator(0), MaxValueValidator(120)]
    )
    helicopter_rate_per_trip = models.FloatField(
        help_text='Helicopter rate per trip (USD)', validators=[MinValueValidator(0), MaxValueValidator(100000)]
    )
    helicopter_fuel_price = models.PositiveIntegerField(
        help_text='Helicopter fuel price (USD/t)', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    helicopter_cruise_speed = models.FloatField(
        help_text='Cruise speed (kn)', validators=[MinValueValidator(100), MaxValueValidator(300)]
    )
    marine_diesel_oil_price = models.PositiveIntegerField(
        help_text='Marine Diesel oil price', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    co2_tax = models.PositiveIntegerField(
        help_text='CO2 tax (USD/t)', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    nox_tax = models.PositiveIntegerField(
        help_text='NOX tax (USD/t)', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    fuel_total_price = models.PositiveIntegerField(
        help_text='Total fuel price (USD/t)', validators=[MinValueValidator(0), MaxValueValidator(10000)]
    )
    fuel_density = models.FloatField(
        help_text='Fuel density (t/m3)', validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    co2_emission_per_tonne_fuel = models.FloatField(
        help_text='CO2 emission per tonne fuel', validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    co2_emission_per_m3_fuel = models.FloatField(
        help_text='CO2 emission per m3 fuel', validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    creator = models.ForeignKey('tenants.User', on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Plan(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    block_name = models.CharField(max_length=255)
    distance_from_tug_base_to_previous_well = models.FloatField(
        verbose_name="Distance from Tug base to previous well (nm)",
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
    )
    reference_operation_jackup = models.ForeignKey(
        'rigs.CustomJackupRig', null=True, blank=True, on_delete=models.CASCADE
    )
    reference_operation_semi = models.ForeignKey('rigs.CustomSemiRig', null=True, blank=True, on_delete=models.CASCADE)
    reference_operation_drillship = models.ForeignKey(
        'rigs.CustomDrillship', null=True, blank=True, on_delete=models.CASCADE
    )
    project = models.ForeignKey("projects.Project", related_name="plans", on_delete=models.CASCADE)
    wells = models.ManyToManyField("wells.CustomWell", through="projects.PlanWellRelation", related_name="plans")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(reference_operation_jackup__isnull=False)
                    & Q(reference_operation_semi__isnull=True)
                    & Q(reference_operation_drillship__isnull=True)
                )
                | (
                    Q(reference_operation_jackup__isnull=True)
                    & Q(reference_operation_semi__isnull=False)
                    & Q(reference_operation_drillship__isnull=True)
                )
                | (
                    Q(reference_operation_jackup__isnull=True)
                    & Q(reference_operation_semi__isnull=True)
                    & Q(reference_operation_drillship__isnull=False)
                ),
                name='single_reference_rig',
            )
        ]

    def __str__(self):
        return self.name


class PlanWellRelation(TimestampedModel):
    plan = models.ForeignKey("projects.Plan", related_name="plan_wells", on_delete=models.CASCADE)
    well = models.ForeignKey("wells.CustomWell", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    distance_from_previous_location = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)], help_text="Distance from previous well (nm)"
    )
    distance_to_helicopter_base = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)], help_text="Distance to Helicopter base (nm)"
    )
    distance_to_psv_base = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)], help_text="Distance to PSV base (nm)"
    )
    distance_to_ahv_base = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)], help_text="Distance to AHV base (nm)"
    )
    distance_to_tug_base = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)], help_text="Distance to Tug base (nm)"
    )
    jackup_positioning_time = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10)], help_text="Jackup positioning time (d)"
    )
    semi_positioning_time = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10)], help_text="Semi positioning time (d)"
    )
    operational_time = models.FloatField(validators=[GreaterThanValidator(0)], help_text="Operational time (d)")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["plan", "well"], name="unique_plan_well_relation"),
            models.UniqueConstraint(
                fields=["plan", "order"], name="unique_plan_well_relation_order", deferrable=models.Deferrable.DEFERRED
            ),
        ]

    def __str__(self):
        return f"Plan Well Relation: {self.well.name}"


class ElementType(models.TextChoices):
    JACKUP_RIG = "JACKUP_RIG", "Jackup Rig"
    SEMI_RIG = "SEMI_RIG", "Semi Rig"
    WELL = "WELL", "Well"
    DRILLSHIP = "DRILLSHIP", "Drillship"
