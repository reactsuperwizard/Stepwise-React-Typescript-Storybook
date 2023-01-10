from django.db import models
from django.db.models import Prefetch, Q

from apps.core.models import TenantAwareModel, TimestampedModel


class MonitorQuerySet(models.QuerySet):
    def with_public_elements(self) -> 'MonitorQuerySet':
        return self.prefetch_related(
            Prefetch('elements', queryset=MonitorElement.objects.filter(draft=False), to_attr='public_elements')
        )


class Monitor(TenantAwareModel, TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    draft = models.BooleanField(
        help_text='Draft monitors will not be visible in the application.',
    )

    objects = MonitorQuerySet.as_manager()

    def __str__(self) -> str:
        return f'Monitor: {self.name}'


class MonitorElement(TimestampedModel):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name='elements')
    name = models.CharField(max_length=255)
    description = models.TextField()
    value_unit = models.CharField(max_length=20)
    value_title = models.CharField(max_length=100)
    draft = models.BooleanField(
        help_text='Draft monitor elements will not be visible in the application.',
    )
    monitor_function = models.ForeignKey(
        'monitors.MonitorFunction', on_delete=models.PROTECT, related_name='monitor_elements'
    )

    def __str__(self) -> str:
        return f'Monitor element: {self.name}'


class MonitorElementPhase(TimestampedModel):
    monitor_element = models.ForeignKey(MonitorElement, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_date = models.DateField(help_text='Phase start date')
    end_date = models.DateField(help_text='Phase end date')
    target = models.FloatField(help_text='Daily target')
    baseline = models.FloatField(help_text='Daily baseline')

    def __str__(self) -> str:
        return f'Monitor element phase: {self.name}'


class MonitorFunctionType(models.TextChoices):
    CO2_EMISSION = 'CO2_EMISSION', 'CO2 emission'
    WIND_SPEED = 'WIND_SPEED', 'Wind speed'
    AIR_TEMPERATURE = 'AIR_TEMPERATURE', 'Air temperature'
    WAVE_HEAVE = 'WAVE_HEAVE', 'Wave heave'


class MonitorFunction(TimestampedModel):
    name = models.CharField(max_length=255)
    draft = models.BooleanField(
        help_text='Draft functions won\'t be calculating values.',
    )
    type = models.CharField(max_length=20, choices=MonitorFunctionType.choices, blank=True)
    monitor_function_source = models.TextField(verbose_name="Monitor function")
    vessel = models.ForeignKey('kims.Vessel', on_delete=models.PROTECT)
    start_date = models.DateTimeField(help_text="Calculation start time")

    def __str__(self) -> str:
        return f'Monitor function: {self.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                condition=~models.Q(type=''),
                fields=["vessel", "type"],
                name="unique_together_monitor_function_vessel_type",
            ),
        ]


class MonitorFunctionValue(TimestampedModel):
    monitor_function = models.ForeignKey(MonitorFunction, on_delete=models.CASCADE)
    value = models.FloatField()
    date = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["monitor_function", "date"], name="unique_monitor_function_value"),
            models.CheckConstraint(
                check=Q(date__minute=0, date__second=0), name="even_monitor_function_value_date_hour"
            ),
        ]
