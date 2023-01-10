import datetime

import factory.fuzzy

from apps.core.factories import CleanDjangoModelFactory


class ConceptEMPElementFactory(CleanDjangoModelFactory):
    name = factory.Sequence(lambda n: f"concept-emp-element-{n}")
    subarea = factory.Faker('word')
    subarea_sensors = factory.Faker('sentence')
    subarea_external_id = factory.Sequence(lambda n: f"sub-area-{n}")
    consumers = factory.Faker('sentence')
    consumer_sensors = factory.Faker('sentence')
    baseline_average_power = factory.fuzzy.FuzzyFloat(5000, 6000)
    target_average_power = factory.fuzzy.FuzzyFloat(3000, 4000)
    percentage_improvement = factory.fuzzy.FuzzyFloat(5, 100)

    class Meta:
        model = 'emps.ConceptEMPElement'


class EMPFactory(CleanDjangoModelFactory):
    name = factory.Sequence(lambda n: f"emp-{n}")
    description = factory.Faker('sentence')
    api_description = factory.Faker('sentence')
    start_date = datetime.date.today() - datetime.timedelta(days=1)
    end_date = datetime.date.today()
    total_rig_baseline_average = factory.fuzzy.FuzzyFloat(5000, 6000)
    total_rig_target_average = factory.fuzzy.FuzzyFloat(3000, 6000)

    class Meta:
        model = 'emps.EMP'


class CustomEMPElementFactory(CleanDjangoModelFactory):
    baseline_average = factory.fuzzy.FuzzyFloat(5000, 6000)
    target_average = factory.fuzzy.FuzzyFloat(3000, 4000)
    emp = factory.SubFactory(EMPFactory)
    concept_emp_element = factory.SubFactory(ConceptEMPElementFactory)

    class Meta:
        model = 'emps.CustomEMPElement'
