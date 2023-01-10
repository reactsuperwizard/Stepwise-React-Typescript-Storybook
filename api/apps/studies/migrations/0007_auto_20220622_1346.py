# Generated by Django 4.0.2 on 2022-06-22 13:46
# Generated by Django 4.0.2 on 2022-06-20 10:18

from django.db import migrations

METRICS_DATA = {
    "tugs_cost": {
        "name": "Total tugs cost",
        "unit": "USD",
    },
    "helicopter_trips": {
        "name": "Total helicopter trips",
        "unit": "",
    },
    "helicopter_fuel": {
        "name": "Total helicopter fuel consumption",
        "unit": "tons",
    },
    "helicopter_co2": {
        "name": "Total helicopter CO2 emission",
        "unit": "tons",
    },
    "helicopter_cost": {
        "name": "Total helicopter cost",
        "unit": "USD",
    },
    "psv_trips": {
        "name": "Total PSV trips",
        "unit": "",
    },
    "psv_fuel": {
        "name": "Total PSV fuel consumption",
        "unit": "tons",
    },
    "psv_cost": {
        "name": "Total PSV cost",
        "unit": "USD",
    },
    "psv_co2": {
        "name": "Total PSV CO2 emission",
        "unit": "tons",
    },
    "cost_per_day": {
        "name": "Day rate",
        "unit": "USD",
    },
    "total_fuel": {
        "name": "Total fuel consumption",
        "unit": "tons",
    },
    "total_cost": {
        "name": "Total cost",
        "unit": "USD",
    },
    "total_co2": {
        "name": "Total CO2 emission",
        "unit": "tons",
    },
}


def set_study_metric_key(apps, _):
    StudyElementModel = apps.get_model('studies', 'StudyElement')
    StudyMetricModel = apps.get_model('studies', 'StudyMetric')

    StudyElementModel.objects.all().delete()
    StudyMetricModel.objects.all().delete()

    for key, data in METRICS_DATA.items():
        StudyMetricModel.objects.create(key=key, **data)


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0006_studyelementjackuprigrelation_rig_plan_co2_and_more'),
    ]

    operations = [migrations.RunPython(set_study_metric_key, migrations.RunPython.noop)]