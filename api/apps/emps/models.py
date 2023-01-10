from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimestampedModel


class ConceptEMPElement(TimestampedModel):
    name = models.CharField(max_length=255)
    subarea = models.CharField(max_length=255)
    subarea_sensors = models.TextField(
        help_text='All sensors that can measure within the sub area that the EMP element address'
    )
    subarea_external_id = models.CharField(max_length=50, help_text='ID used to identify sub area in external systems')
    consumers = models.TextField(
        help_text='Overview of what consumers are affected and should be measured directly or indirectly'
    )
    consumer_sensors = models.TextField(help_text='Sensors that are available on the equipment ')
    baseline_average_power = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Baseline average MW")
    target_average_power = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Target average MW")
    percentage_improvement = models.FloatField()

    class Meta:
        verbose_name = 'Concept EMP element'

    def __str__(self) -> str:
        return self.name


class CustomEMPElement(TimestampedModel):
    baseline_average = models.FloatField(validators=[MinValueValidator(0)])
    target_average = models.FloatField(validators=[MinValueValidator(0)])
    emp = models.ForeignKey('emps.EMP', on_delete=models.CASCADE, related_name='elements')
    concept_emp_element = models.ForeignKey('emps.ConceptEMPElement', on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["emp", "concept_emp_element"], name="unique_custom_emp_element")]


class EMP(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    api_description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    total_rig_baseline_average = models.FloatField(validators=[MinValueValidator(0)])
    total_rig_target_average = models.FloatField(validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return self.name
