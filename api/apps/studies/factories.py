import factory.fuzzy

JACKUP_STUDY_METRIC_KEYS = (
    "tugs_cost",
    "helicopter_trips",
    "helicopter_fuel",
    "helicopter_co2",
    "helicopter_cost",
    "psv_trips",
    "psv_fuel",
    "psv_cost",
    "psv_co2",
    "total_fuel",
    "total_cost",
    "total_co2",
    "cost_per_meter",
    "total_days",
)

SEMI_STUDY_METRIC_KEYS = (
    "ahv_cost",
    "helicopter_trips",
    "helicopter_fuel",
    "helicopter_co2",
    "helicopter_cost",
    "psv_trips",
    "psv_fuel",
    "psv_cost",
    "psv_co2",
    "tugs_cost",
    "total_fuel",
    "total_cost",
    "total_co2",
    "total_logistic_cost",
    "total_move_cost",
    "total_fuel_cost",
    "total_transit_co2",
    "total_support_co2",
    "total_rig_and_spread_cost",
    "cost_per_meter",
    "total_days",
)


class StudyMetricFactory(factory.django.DjangoModelFactory):
    name = factory.sequence(lambda n: f"metric-name-{n}")
    key = factory.fuzzy.FuzzyChoice(set(JACKUP_STUDY_METRIC_KEYS) & set(SEMI_STUDY_METRIC_KEYS))
    unit = "MW"
    is_jackup_compatible = True
    is_semi_compatible = True
    is_drillship_compatible = True

    class Meta:
        model = "studies.StudyMetric"
        django_get_or_create = ('key',)


class StudyElementFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory("apps.projects.factories.ProjectFactory")
    title = factory.Sequence(lambda n: f"element-{n}")
    metric = factory.SubFactory(StudyMetricFactory)
    plan = factory.SubFactory("apps.projects.factories.PlanFactory")
    creator = factory.SubFactory('apps.tenants.factories.UserFactory')

    class Meta:
        model = "studies.StudyElement"


class StudyElementRigRelationFactory(factory.django.DjangoModelFactory):
    study_element = factory.SubFactory(StudyElementFactory)
    value = factory.fuzzy.FuzzyFloat(low=100, high=200)


class StudyElementSemiRigRelationFactory(StudyElementRigRelationFactory):
    rig = factory.SubFactory("apps.rigs.factories.CustomSemiRigFactory")
    rig_plan_co2 = factory.SubFactory("apps.rigs.factories.CustomSemiPlanCO2Factory")

    class Meta:
        model = "studies.StudyElementSemiRigRelation"


class StudyElementJackupRigRelationFactory(StudyElementRigRelationFactory):
    rig = factory.SubFactory("apps.rigs.factories.CustomJackupRigFactory")
    rig_plan_co2 = factory.SubFactory("apps.rigs.factories.CustomJackupPlanCO2Factory")

    class Meta:
        model = "studies.StudyElementJackupRigRelation"


class StudyElementDrillshipRelationFactory(StudyElementRigRelationFactory):
    rig = factory.SubFactory("apps.rigs.factories.CustomDrillshipFactory")

    class Meta:
        model = "studies.StudyElementDrillshipRelation"
