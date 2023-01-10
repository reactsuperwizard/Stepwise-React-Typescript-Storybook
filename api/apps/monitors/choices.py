from django.db import models


class MonitorElementDatasetType(models.TextChoices):
    DAILY = 'DAILY', 'Daily'
    CUMULATIVE = 'CUMULATIVE', 'Cumulative'
