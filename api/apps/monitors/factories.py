import datetime
from typing import TypedDict

import factory.fuzzy
from django.utils import timezone

from apps.monitors.models import Monitor, MonitorElement, MonitorElementPhase, MonitorFunction, MonitorFunctionValue

MONITOR_FUNCTION_SOURCE = """
def monitor(tags):
    return 0
"""


class MonitorFactory(factory.django.DjangoModelFactory):
    tenant = factory.SubFactory('apps.tenants.factories.TenantFactory')
    name = factory.Sequence(lambda n: f"monitor-{n}")
    description = factory.Faker('sentence')
    start_date = factory.fuzzy.FuzzyDateTime(start_dt=timezone.now() - datetime.timedelta(days=30))
    end_date = factory.fuzzy.FuzzyDateTime(start_dt=timezone.now(), end_dt=timezone.now() + datetime.timedelta(days=30))
    draft = False

    class Meta:
        model = Monitor


class MonitorElementFactory(factory.django.DjangoModelFactory):
    monitor = factory.SubFactory(MonitorFactory)
    name = factory.Sequence(lambda n: f"monitor-element-{n}")
    description = factory.Faker('sentence')
    value_title = "Energy (MW)"
    value_unit = "MW"
    draft = False
    monitor_function = factory.SubFactory('apps.monitors.factories.MonitorFunctionFactory')

    class Meta:
        model = MonitorElement


class MonitorElementPhaseFactory(factory.django.DjangoModelFactory):
    monitor_element = factory.SubFactory(MonitorElementFactory)
    name = factory.Sequence(lambda n: f"Phase {n}")
    start_date = factory.LazyAttribute(lambda o: o.monitor_element.monitor.start_date.date())
    end_date = factory.LazyAttribute(lambda o: o.monitor_element.monitor.end_date.date())
    target = 30
    baseline = 40

    class Meta:
        model = MonitorElementPhase


class MonitorFunctionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Monitor function {n}")
    draft = False
    monitor_function_source = MONITOR_FUNCTION_SOURCE
    vessel = factory.SubFactory('apps.kims.factories.VesselFactory')
    start_date = factory.fuzzy.FuzzyDateTime(start_dt=timezone.now() - datetime.timedelta(days=30))

    class Meta:
        model = MonitorFunction


class MonitorFunctionValueFactory(factory.django.DjangoModelFactory):
    monitor_function = factory.SubFactory(MonitorFunctionFactory)
    value = factory.fuzzy.FuzzyFloat(0, 100)
    date = factory.LazyFunction(lambda: timezone.now().replace(minute=0, second=0, microsecond=0))

    class Meta:
        model = MonitorFunctionValue


class MonitorElementData(TypedDict):
    date: datetime.date
    baseline: float
    target: float
    current: float | None
