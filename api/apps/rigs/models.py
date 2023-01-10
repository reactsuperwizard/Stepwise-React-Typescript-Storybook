import datetime
from typing import cast

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Value

from apps.core.models import TenantAwareModel, TimestampedModel
from apps.core.validators import MaxDateValidator, MinDateValidator
from apps.projects.models import ElementType


class HighMediumLow(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class RigStatus(models.TextChoices):
    DRILLING = "DRILLING", "Drilling"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION", "Under Construction"
    WARM_STACKED = "WARM_STACKED", "Warm Stacked"
    COLD_STACKED = "COLD_STACKED", "Cold Stacked"
    MOBILIZING = "MOBILIZING", "Mobilizing"


class TopsideDesign(models.TextChoices):
    NOV = "NOV", "NOV"
    MH = "MH", "MH"
    CAMERON = "CAMERON", "Cameron"
    OTHER = "OTHER", "Other"


class AbstractCustomRig(TenantAwareModel):
    creator = models.ForeignKey('tenants.User', on_delete=models.PROTECT)
    emp = models.OneToOneField("emps.EMP", null=True, blank=True, on_delete=models.SET_NULL)
    draft = models.BooleanField()

    class Meta:
        abstract = True


def AbstractRigFactory(draft: bool) -> type[models.Model]:
    class AbstractRig(TimestampedModel):
        name = models.CharField(max_length=255, verbose_name="Name", blank=draft)
        manager = models.CharField(max_length=255, verbose_name="Manager", blank=draft)
        design = models.CharField(max_length=255, verbose_name="Design", blank=draft)
        build_yard = models.CharField(max_length=255, verbose_name="Build yard", blank=draft)
        rig_status = models.CharField(max_length=32, choices=RigStatus.choices, verbose_name="Rig status", blank=draft)
        delivery_date = models.DateField(
            verbose_name="Delivery Date",
            blank=draft,
            null=draft,
            validators=[
                MinDateValidator(datetime.date(year=1970, month=1, day=1)),
                MaxDateValidator(datetime.date(year=2025, month=12, day=31)),
            ],
        )
        special_survey_due = models.DateField(
            verbose_name="Special Survey Due",
            null=draft,
            blank=draft,
            validators=[
                MinDateValidator(datetime.date(year=2022, month=1, day=1)),
                MaxDateValidator(datetime.date(year=2027, month=12, day=31)),
            ],
        )
        end_of_last_contract = models.DateField(
            verbose_name="End of last contract",
            null=draft,
            blank=draft,
            validators=[
                MinDateValidator(datetime.date(year=1970, month=1, day=1)),
                MaxDateValidator(datetime.date(year=2035, month=12, day=31)),
            ],
        )
        months_in_operation_last_year = models.PositiveIntegerField(
            validators=[MaxValueValidator(12)], verbose_name="Months in operation last year", null=draft, blank=draft
        )
        months_in_operation_last_3_years = models.PositiveIntegerField(
            validators=[MaxValueValidator(36)], verbose_name="Months in operation last 3 years", null=draft, blank=draft
        )
        design_score = models.CharField(
            max_length=16, choices=HighMediumLow.choices, verbose_name="Design score", blank=draft
        )
        topside_design = models.CharField(
            max_length=8, choices=TopsideDesign.choices, verbose_name="Topside design", blank=draft
        )
        quarters_capacity = models.FloatField(
            validators=[MinValueValidator(10), MaxValueValidator(400)],
            verbose_name="Quarters capacity",
            null=draft,
            blank=draft,
        )
        hull_breadth = models.FloatField(
            validators=[MinValueValidator(100), MaxValueValidator(500)],
            null=draft,
            blank=draft,
            verbose_name="Hull breadth (ft)",
        )
        hull_depth = models.FloatField(
            validators=[MinValueValidator(10), MaxValueValidator(200)],
            null=draft,
            blank=draft,
            verbose_name="Hull depth (ft)",
        )
        hull_length = models.FloatField(
            validators=[MinValueValidator(100), MaxValueValidator(500)],
            null=draft,
            blank=draft,
            verbose_name="Hull length (ft)",
        )
        derrick_height = models.FloatField(
            validators=[
                MinValueValidator(50),
                MaxValueValidator(300),
            ],
            verbose_name="Derrick height (ft)",
            null=draft,
            blank=draft,
        )
        derrick_capacity = models.FloatField(
            validators=[
                MinValueValidator(500000),
                MaxValueValidator(3000000),
            ],
            verbose_name="Derrick capacity (lbs)",
            null=draft,
            blank=draft,
        )
        drawworks_power = models.FloatField(
            validators=[MinValueValidator(1000), MaxValueValidator(10000)],
            verbose_name="Drawworks power (HP)",
            null=draft,
            blank=draft,
        )
        total_cranes = models.FloatField(
            validators=[MinValueValidator(1), MaxValueValidator(10)],
            verbose_name="Total cranes",
            null=draft,
            blank=draft,
        )
        crane_capacity = models.FloatField(
            validators=[MinValueValidator(10), MaxValueValidator(500)],
            verbose_name="Crane capacity",
            null=draft,
            blank=draft,
        )
        total_bop_rams = models.FloatField(
            validators=[MinValueValidator(1), MaxValueValidator(10)],
            verbose_name="Total BOP rams",
            null=draft,
            blank=draft,
        )
        bop_diameter_wp_max = models.FloatField(
            validators=[MinValueValidator(10), MaxValueValidator(30)],
            verbose_name="BOP diameter WP Max (in)",
            null=draft,
            blank=draft,
        )
        bop_wp_max = models.FloatField(
            validators=[MinValueValidator(5000), MaxValueValidator(25000)],
            verbose_name="BOP WP Max (psi)",
            null=draft,
            blank=draft,
        )
        number_of_bop_stacks = models.FloatField(
            validators=[MinValueValidator(1), MaxValueValidator(3)],
            verbose_name="Number of BOP stacks",
            null=draft,
            blank=draft,
        )
        mudpump_quantity = models.IntegerField(
            validators=[MinValueValidator(1), MaxValueValidator(10)],
            verbose_name="Mudpump quantity",
            null=draft,
            blank=draft,
        )
        liquid_mud = models.FloatField(
            validators=[MinValueValidator(1000), MaxValueValidator(30000)],
            verbose_name="Liquid mud (bbl)",
            null=draft,
            blank=draft,
        )
        mud_total_power = models.FloatField(
            validators=[MinValueValidator(1000), MaxValueValidator(20000)],
            verbose_name="Mud total (HP)",
            null=draft,
            blank=draft,
        )
        shaleshaker_total = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Shaleshaker total",
            null=draft,
            blank=draft,
        )
        engine_power = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name="Engine power (HP)",
            null=draft,
            blank=draft,
        )
        engine_quantity = models.PositiveIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Engine quantity",
            null=draft,
            blank=draft,
        )
        engine_total = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100000)], null=draft, blank=draft
        )
        generator_power = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name="Generator power (kW)",
            null=draft,
            blank=draft,
        )
        generator_quantity = models.PositiveIntegerField(
            validators=[MaxValueValidator(10)], verbose_name="Generator quantity", null=draft, blank=draft
        )
        generator_total = models.FloatField(
            validators=[MinValueValidator(0), MaxValueValidator(100000)],
            verbose_name="Generator total",
            null=draft,
            blank=draft,
        )
        offline_stand_building = models.BooleanField(verbose_name="Offline stand building", null=draft, blank=draft)
        auto_pipe_handling = models.BooleanField(verbose_name="Auto pipe handling", null=draft, blank=draft)
        dual_activity = models.BooleanField(verbose_name="Dual activity", null=draft, blank=draft)
        drilltronic = models.BooleanField(verbose_name="Drilltronic", null=draft, blank=draft)
        dynamic_drilling_guide = models.BooleanField(verbose_name="Dynamic drilling guide", null=draft, blank=draft)
        process_automation_platform = models.BooleanField(
            verbose_name="Process automation platform", null=draft, blank=draft
        )
        automatic_tripping = models.BooleanField(verbose_name="Automatic tripping", null=draft, blank=draft)
        closed_bus = models.BooleanField(verbose_name="Closed bus", null=draft, blank=draft)
        scr = models.BooleanField(verbose_name="SCR", null=draft, blank=draft)
        hybrid = models.BooleanField(verbose_name="Hybrid", null=draft, blank=draft)
        hvac_heat_recovery = models.BooleanField(verbose_name="HVAC heat recovery", null=draft, blank=draft)
        freshwater_cooling_systems = models.BooleanField(
            verbose_name="Freshwater cooling systems", null=draft, blank=draft
        )
        seawater_cooling_systems = models.BooleanField(verbose_name="Seawater cooling systems", null=draft, blank=draft)
        operator_awareness_dashboard = models.BooleanField(
            verbose_name="Operator awareness dashboard", null=draft, blank=draft
        )
        hpu_optimization = models.BooleanField(verbose_name="HPU optimization", null=draft, blank=draft)
        optimized_heat_tracing_system = models.BooleanField(
            verbose_name="Optimized heat tracing system", null=draft, blank=draft
        )
        floodlighting_optimization = models.BooleanField(
            verbose_name="Floodlighting optimization", null=draft, blank=draft
        )
        vfds_on_aux_machinery = models.BooleanField(verbose_name="VFD's on AUX machinery", null=draft, blank=draft)
        day_rate = models.FloatField(
            blank=True,
            null=True,
            validators=[MinValueValidator(0), MaxValueValidator(1000000)],
            verbose_name="Day rate (USD/d)",
        )
        spread_cost = models.FloatField(
            verbose_name="Spread cost (USD)",
            blank=True,
            null=True,
            validators=[MinValueValidator(0), MaxValueValidator(1000000)],
        )
        tugs_no_used = models.PositiveIntegerField(
            help_text="Number of tugs to be used",
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(10)],
        )

        class Meta:
            abstract = True

        def __str__(self):
            return self.name

    return AbstractRig


class DPClass(models.TextChoices):
    DP2 = "DP2", "DP2"
    DP3 = "DP3", "DP3"
    DP_ER = "DP-ER", "DP-ER"


class Airgap(models.TextChoices):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


def AbstractSemiRigFactory(draft: bool) -> type[models.Model]:
    class AbstractSemiRig(AbstractRigFactory(draft)):  # type: ignore
        variable_load = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name="Variable load (t)",
            null=draft,
            blank=draft,
        )
        rig_water_depth = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(12000)],
            verbose_name="Rig water depth(ft)",
            null=draft,
            blank=draft,
        )
        equipment_load = models.CharField(  # type: ignore
            max_length=16, choices=HighMediumLow.choices, verbose_name="Equipment load", blank=draft
        )
        drillfloor_efficiency = models.CharField(  # type: ignore
            max_length=16, choices=HighMediumLow.choices, verbose_name="Drillfloor efficiency", blank=draft
        )
        hull_concept_score = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Hull concept score",
            null=draft,
            blank=draft,
        )
        hull_design_eco_score = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Hull design eco score",
            null=draft,
            blank=draft,
        )
        dp = models.BooleanField(verbose_name="DP", null=draft, blank=draft)  # type: ignore
        dp_class = models.CharField(
            max_length=8, choices=DPClass.choices, verbose_name="DP Class", blank=draft
        )  # type: ignore
        thruster_assist = models.BooleanField(verbose_name="Thruster assist", null=draft, blank=draft)  # type: ignore
        total_anchors = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(16)],
            verbose_name="Total anchors",
            null=draft,
            blank=draft,
        )
        anchor_standalone = models.BooleanField(
            verbose_name="Anchor standalone", null=draft, blank=draft
        )  # type: ignore
        airgap = models.CharField(
            max_length=16, choices=Airgap.choices, verbose_name="Airgap", blank=draft
        )  # type: ignore
        draft_depth = models.FloatField(  # type: ignore
            validators=[
                MinValueValidator(50),
                MaxValueValidator(150),
            ],
            verbose_name="Draft (ft)",
            null=draft,
            blank=draft,
        )
        displacement = models.FloatField(  # type: ignore
            validators=[
                MinValueValidator(5000),
                MaxValueValidator(300000),
            ],
            verbose_name="Displacement",
            null=draft,
            blank=draft,
        )

        dual_derrick = models.BooleanField(verbose_name="Dual derrick", null=draft, blank=draft)  # type: ignore
        active_heave_drawwork = models.BooleanField(
            verbose_name="Active heave drawwork", null=draft, blank=draft
        )  # type: ignore
        cmc_with_active_heave = models.BooleanField(
            verbose_name="CMC with active heave", null=draft, blank=draft
        )  # type: ignore
        ram_system = models.BooleanField(verbose_name="RAM system", null=draft, blank=draft)  # type: ignore
        tripsaver = models.BooleanField(verbose_name="Tripsaver", null=draft, blank=draft)  # type: ignore
        move_speed = models.FloatField(  # type: ignore
            help_text="Move speed (kn)",
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(10)],
        )

        class Meta:
            abstract = True

    return AbstractSemiRig


def AbstractJackupRigFactory(draft: bool) -> type[models.Model]:
    class AbstractJackupRig(AbstractRigFactory(draft)):  # type: ignore
        variable_load = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name="Variable load (t)",
            null=draft,
            blank=draft,
        )
        rig_water_depth = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(500)],
            verbose_name="Rig water depth(ft)",
            null=draft,
            blank=draft,
        )
        cantilever_reach = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(150)],
            verbose_name="Cantilever reach (ft)",
            null=draft,
            blank=draft,
        )
        cantilever_lateral = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(50)],
            verbose_name="Cantilever lateral (ft)",
            null=draft,
            blank=draft,
        )
        cantilever_capacity = models.FloatField(  # type: ignore
            validators=[MinValueValidator(1000000), MaxValueValidator(5000000)], null=draft, blank=draft
        )
        leg_length = models.FloatField(  # type: ignore
            validators=[MinValueValidator(100), MaxValueValidator(1000)],
            verbose_name="Leg length (ft)",
            null=draft,
            blank=draft,
        )
        leg_spacing = models.FloatField(  # type: ignore
            validators=[MinValueValidator(100), MaxValueValidator(300)],
            verbose_name="Leg spacing (ft)",
            null=draft,
            blank=draft,
        )
        subsea_drilling = models.BooleanField(verbose_name="Subsea drilling", null=draft, blank=draft)  # type: ignore
        enhanced_legs = models.BooleanField(verbose_name="Enhanced legs", null=draft, blank=draft)  # type: ignore
        jack_up_time = models.FloatField(  # type: ignore
            verbose_name="Jack up time (d)",
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(10)],
        )
        jack_down_time = models.FloatField(  # type: ignore
            verbose_name="Jack down to move time (d)",
            null=draft,
            blank=draft,
            validators=[MinValueValidator(0), MaxValueValidator(10)],
        )

        class Meta:
            abstract = True

    return AbstractJackupRig


class ConceptSemiRig(AbstractSemiRigFactory(False)):  # type: ignore
    pass


class ConceptJackupRig(AbstractJackupRigFactory(False)):  # type: ignore
    pass


class RigType(models.TextChoices):
    JACKUP = "JACKUP", "Jackup"
    SEMI = "SEMI", "Semi"
    DRILLSHIP = "DRILLSHIP", "Drillship"


class CustomSemiRigQuerySet(models.QuerySet):
    def with_type(self):
        return cast('CustomSemiRigQuerySet', self.annotate(type=Value(RigType.SEMI)))

    def with_element_type(self):
        return cast('CustomSemiRigQuerySet', self.annotate(element_type=Value(ElementType.SEMI_RIG)))

    def studiable(self) -> 'CustomSemiRigQuerySet':
        return self.filter(Q(dp=True) | Q(thruster_assist=True))


class CustomSemiRig(AbstractSemiRigFactory(True), AbstractCustomRig):  # type: ignore
    project = models.ForeignKey(
        'projects.Project', blank=True, null=True, on_delete=models.CASCADE, related_name="semi_rigs"
    )

    type = RigType.SEMI
    objects = CustomSemiRigQuerySet.as_manager()


class CustomJackupRigQuerySet(models.QuerySet):
    def with_type(self):
        return cast('CustomJackupRigQuerySet', self.annotate(type=Value(RigType.JACKUP)))

    def with_element_type(self):
        return cast('CustomJackupRigQuerySet', self.annotate(element_type=Value(ElementType.JACKUP_RIG)))

    def studiable(self) -> 'CustomJackupRigQuerySet':
        return self


class CustomJackupRig(AbstractJackupRigFactory(True), AbstractCustomRig):  # type: ignore
    project = models.ForeignKey(
        'projects.Project', blank=True, null=True, on_delete=models.CASCADE, related_name="jackup_rigs"
    )

    type = RigType.JACKUP
    objects = CustomJackupRigQuerySet.as_manager()


def AbstractDrillshipFactory(draft: bool) -> type[models.Model]:
    class AbstractDrillship(AbstractRigFactory(draft)):  # type: ignore
        equipment_load = models.CharField(  # type: ignore
            max_length=16, choices=HighMediumLow.choices, verbose_name="Equipment load", blank=draft
        )
        drillfloor_efficiency = models.CharField(  # type: ignore
            max_length=16, choices=HighMediumLow.choices, verbose_name="Drillfloor efficiency", blank=draft
        )
        rig_water_depth = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(20000)],
            verbose_name="Rig water depth(ft)",
            null=draft,
            blank=draft,
        )
        variable_load = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(50000)],
            verbose_name="Variable load (t)",
            null=draft,
            blank=draft,
        )
        hull_concept_score = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Hull concept score",
            null=draft,
            blank=draft,
        )
        hull_design_eco_score = models.FloatField(  # type: ignore
            validators=[MinValueValidator(0), MaxValueValidator(10)],
            verbose_name="Hull design eco score",
            null=draft,
            blank=draft,
        )
        dp = models.BooleanField(verbose_name="DP", null=draft, blank=draft)  # type: ignore
        dp_class = models.CharField(
            max_length=8, choices=DPClass.choices, verbose_name="DP Class", blank=draft
        )  # type: ignore
        draft_depth = models.FloatField(  # type: ignore
            validators=[
                MinValueValidator(50),
                MaxValueValidator(150),
            ],
            verbose_name="Draft (ft)",
            null=draft,
            blank=draft,
        )
        displacement = models.FloatField(  # type: ignore
            validators=[
                MinValueValidator(5000),
                MaxValueValidator(300000),
            ],
            verbose_name="Displacement",
            null=draft,
            blank=draft,
        )
        riser_on_board_outfitted = models.FloatField(  # type: ignore
            validators=[
                MinValueValidator(0),
                MaxValueValidator(20000),
            ],
            verbose_name='Riser on board outfitted',
            null=draft,
            blank=draft,
        )
        riser_storage_inside_hull = models.BooleanField(  # type: ignore
            verbose_name='Riser storage inside hull',
            null=draft,
            blank=draft,
        )
        split_funnels_free_stern_deck = models.BooleanField(  # type: ignore
            verbose_name='Split funnels / free stern deck',
            null=draft,
            blank=draft,
        )
        dual_derrick = models.BooleanField(verbose_name="Dual derrick", null=draft, blank=draft)  # type: ignore
        active_heave_drawwork = models.BooleanField(
            verbose_name="Active heave drawwork", null=draft, blank=draft
        )  # type: ignore
        cmc_with_active_heave = models.BooleanField(
            verbose_name="CMC with active heave", null=draft, blank=draft
        )  # type: ignore
        ram_system = models.BooleanField(verbose_name="RAM system", null=draft, blank=draft)  # type: ignore
        tripsaver = models.BooleanField(verbose_name="Tripsaver", null=draft, blank=draft)  # type: ignore

        class Meta:
            abstract = True

    return AbstractDrillship


class ConceptDrillship(AbstractDrillshipFactory(False)):  # type: ignore
    pass


class CustomDrillshipQuerySet(models.QuerySet):
    def with_type(self):
        return cast('CustomDrillshipQuerySet', self.annotate(type=Value(RigType.DRILLSHIP)))

    def with_element_type(self):
        return cast('CustomDrillshipQuerySet', self.annotate(element_type=Value(ElementType.DRILLSHIP)))

    def studiable(self) -> 'CustomDrillshipQuerySet':
        return self.none()


class CustomDrillship(AbstractDrillshipFactory(True), AbstractCustomRig):  # type: ignore
    project = models.ForeignKey(
        'projects.Project', blank=True, null=True, on_delete=models.CASCADE, related_name="drillships"
    )

    type = RigType.DRILLSHIP
    objects = CustomDrillshipQuerySet.as_manager()


class AbstractRigSubareaScore(TimestampedModel):
    rig_status = models.FloatField()
    topside_efficiency = models.FloatField()
    deck_efficiency = models.FloatField()
    capacities = models.FloatField()
    co2 = models.FloatField()

    class Meta:
        abstract = True


class CustomJackupSubareaScoreManager(models.Manager):
    def get_or_calculate(self, rig: CustomJackupRig) -> 'CustomJackupSubareaScore':
        from .services.apis import sync_custom_jackup_subarea_score

        try:
            return rig.subarea_score
        except CustomJackupSubareaScore.DoesNotExist:
            return sync_custom_jackup_subarea_score(rig)


class CustomJackupSubareaScore(AbstractRigSubareaScore):
    rig = models.OneToOneField(CustomJackupRig, on_delete=models.CASCADE, related_name="subarea_score")
    move_and_installation = models.FloatField()
    objects = CustomJackupSubareaScoreManager()

    def __str__(self):
        return f"Jackup subarea score: {self.pk}"

    @property
    def efficiency(self) -> float:
        return (
            sum(
                [
                    self.rig_status,
                    self.deck_efficiency,
                    self.topside_efficiency,
                    self.capacities,
                    self.move_and_installation,
                ]
            )
            / 5
        )


class CustomSemiSubareaScoreManager(models.Manager):
    def get_or_calculate(self, rig: CustomSemiRig) -> 'CustomSemiSubareaScore':
        from .services.apis import sync_custom_semi_subarea_score

        try:
            return rig.subarea_score
        except CustomSemiSubareaScore.DoesNotExist:
            return sync_custom_semi_subarea_score(rig)


class CustomSemiSubareaScore(AbstractRigSubareaScore):
    rig = models.OneToOneField(CustomSemiRig, on_delete=models.CASCADE, related_name="subarea_score")
    wow = models.FloatField()
    objects = CustomSemiSubareaScoreManager()

    def __str__(self):
        return f"Semi subarea score: {self.pk}"

    @property
    def efficiency(self) -> float:
        return (
            sum(
                [
                    self.rig_status,
                    self.deck_efficiency,
                    self.topside_efficiency,
                    self.capacities,
                    self.wow,
                ]
            )
            / 5
        )


class AbstractRigPlanCO2(TimestampedModel):
    plan = models.ForeignKey('projects.Plan', on_delete=models.CASCADE)
    helicopter_trips = models.FloatField(null=True, blank=True, help_text="Number of helicopter trips")
    helicopter_fuel = models.FloatField(null=True, blank=True, help_text="Total helicopter fuel consumption (tons)")
    helicopter_cost = models.FloatField(null=True, blank=True, help_text="Total helicopter cost (USD)")
    helicopter_co2 = models.FloatField(null=True, blank=True, help_text="Total Helicopter CO2 emission (tons)")
    psv_trips = models.FloatField(null=True, blank=True, help_text="Number of PSV trips")
    psv_fuel = models.FloatField(null=True, blank=True, help_text="Total PSV fuel consumption (tons)")
    psv_cost = models.FloatField(null=True, blank=True, help_text="Total PSV CO2 cost (USD)")
    psv_co2 = models.FloatField(null=True, blank=True, help_text="Total PSV CO2 emission (tons)")
    total_fuel = models.FloatField(null=True, blank=True, help_text="Total fuel consumption (tons)")
    total_cost = models.FloatField(null=True, blank=True, help_text="Total cost (USD)")
    total_co2 = models.FloatField(null=True, blank=True, help_text="Total CO2 emission (tons)")
    tugs_cost = models.FloatField(null=True, blank=True, help_text="Total tugs cost (USD)")
    cost_per_meter = models.FloatField(null=True, blank=True, help_text="Cost per meter (USD)")
    total_days = models.FloatField(null=True, blank=True, help_text="Total days")

    class Meta:
        abstract = True


class CustomJackupPlanCO2(AbstractRigPlanCO2):
    rig = models.ForeignKey(CustomJackupRig, on_delete=models.CASCADE, related_name="co2_plans")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["plan", "rig"], name="unique_custom_jackup_plan_co2")]
        verbose_name = "Custom Jackup Plan CO2"
        verbose_name_plural = "Custom Jackup Plan CO2's"

    def __str__(self):
        return f"Custom jackup plan CO2: {self.pk}"


class CustomSemiPlanCO2(AbstractRigPlanCO2):
    rig = models.ForeignKey(CustomSemiRig, on_delete=models.CASCADE, related_name="co2_plans")
    ahv_cost = models.FloatField(null=True, blank=True, help_text="Total AHV cost (USD)")
    total_logistic_cost = models.FloatField(null=True, blank=True, help_text="Total logistic cost (USD)")
    total_move_cost = models.FloatField(null=True, blank=True, help_text="Total move cost (USD)")
    total_fuel_cost = models.FloatField(null=True, blank=True, help_text="Total fuel cost (USD)")
    total_transit_co2 = models.FloatField(null=True, blank=True, help_text="Total transit CO2 emission (tons)")
    total_support_co2 = models.FloatField(null=True, blank=True, help_text="Total support CO2 emission (tons)")
    total_rig_and_spread_cost = models.FloatField(null=True, blank=True, help_text="Total rig and spread cost (USD)")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["plan", "rig"], name="unique_custom_semi_plan_co2")]
        verbose_name = "Custom Semi Plan CO2"
        verbose_name_plural = "Custom Semi Plan CO2's"

    def __str__(self):
        return f"Custom semi plan CO2: {self.pk}"
