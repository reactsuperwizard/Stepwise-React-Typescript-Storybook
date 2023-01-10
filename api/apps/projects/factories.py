import factory.fuzzy

from apps.core.factories import CleanDjangoModelFactory
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import CustomWellFactory


class ProjectFactory(CleanDjangoModelFactory):
    name = factory.Sequence(lambda n: f'project-{n}')
    description = factory.Faker('sentence')
    creator = factory.SubFactory(UserFactory)
    tenant = factory.SubFactory(TenantFactory)
    tugs_day_rate = 300.0
    tugs_avg_move_fuel_consumption = 23.5
    tugs_avg_transit_fuel_consumption = 10.3
    tugs_move_speed = 5.5
    tugs_transit_speed = 21.3
    ahv_no_used = 5
    ahv_no_days_per_location = 7.5
    ahv_avg_fuel_consumption = 3.2
    ahv_day_rate = 1000.0
    psv_calls_per_week = 2
    psv_types = 'PS 213, PSV 153'
    psv_avg_fuel_transit_consumption = 12.6
    psv_avg_fuel_dp_consumption = 5.5
    psv_day_rate = 7000.0
    psv_speed = 12.0
    psv_loading_time = 0.25
    psv_fuel_price = 1333.33
    helicopter_no_flights_per_week = 7
    helicopter_types = 'UH-60 Black Hawk'
    helicopter_cruise_speed = 120.0
    helicopter_avg_fuel_consumption = 12
    helicopter_rate_per_trip = 200.0
    helicopter_fuel_price = 3333.13
    marine_diesel_oil_price = 3000.0
    co2_tax = 60.5
    nox_tax = 88.0
    fuel_total_price = 3456.0
    fuel_density = 3.6
    co2_emission_per_tonne_fuel = 4.4
    co2_emission_per_m3_fuel = 3.13

    @factory.post_generation
    def wells(self, create: bool, extracted: tuple[CustomWellFactory, ...] | None, **kwargs: str) -> None:
        if not create:
            return

        if extracted:
            self.wells.set(extracted)

    class Meta:
        model = 'projects.Project'


class PlanFactory(CleanDjangoModelFactory):
    name = factory.Sequence(lambda n: f'plan-{n}')
    description = factory.Faker('sentence')
    block_name = factory.Sequence(lambda n: f'block-name-{n}')
    reference_operation_jackup = factory.SubFactory('apps.rigs.factories.CustomJackupRigFactory')
    reference_operation_semi = None
    reference_operation_drillship = None
    project = factory.SubFactory(ProjectFactory)
    distance_from_tug_base_to_previous_well = 100.0

    class Meta:
        model = 'projects.Plan'


class PlanWellRelationFactory(CleanDjangoModelFactory):
    plan = factory.SubFactory(PlanFactory)
    well = factory.SubFactory('apps.wells.factories.CustomWellFactory')
    order = factory.LazyAttribute(lambda obj: obj.plan.wells.count())
    distance_from_previous_location = 10.1
    distance_to_helicopter_base = 20.2
    distance_to_psv_base = 30.3
    distance_to_ahv_base = 40.4
    distance_to_tug_base = 50.5
    jackup_positioning_time = 1.6
    semi_positioning_time = 1.7
    operational_time = 20

    class Meta:
        model = 'projects.PlanWellRelation'
