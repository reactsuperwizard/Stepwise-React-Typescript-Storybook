from typing import cast

import pgcrypto
from django.db import models
from django.db.models import Q

from apps.core.models import TimestampedModel


class KimsAPI(TimestampedModel):
    username = pgcrypto.EncryptedCharField(help_text='K-IMS API username')
    password = pgcrypto.EncryptedCharField(help_text='K-IMS API password')
    base_url = models.URLField(help_text='K-IMS API base URL')

    class Meta:
        verbose_name = 'K-IMS API'

    def __str__(self):
        return self.base_url


class Vessel(TimestampedModel):
    kims_api = models.ForeignKey(KimsAPI, on_delete=models.PROTECT)
    kims_vessel_id = models.CharField(
        max_length=255, verbose_name="K-IMS Vessel ID", help_text="Vessel ID in the K-IMS system."
    )
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=False, help_text="Data will be synced only for active vessels.")
    tags_synced_at = models.DateTimeField(null=True, help_text="Time of the last sync of tag values")

    def __str__(self) -> str:
        return self.name


class TagDataType(models.TextChoices):
    DOUBLE = "Double", "Double"
    OBJECT = "Object", "Object"
    BOOLEAN = "Boolean", "Boolean"
    SINGLE = "Single", "Single"
    INT_32 = "Int32", "Int32"


class Tag(TimestampedModel):
    name = models.CharField(max_length=255, help_text="Name of the tag in the KIMS system.")
    vessel = models.ForeignKey('kims.Vessel', on_delete=models.PROTECT, related_name="tags")
    data_type = models.CharField(max_length=255, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["name", "vessel"], name="unique_vessel_tag_relation")]

    def __str__(self) -> str:
        return self.name


class TagValueQuerySet(models.QuerySet):
    def with_data_type(self):
        return cast('TagValueQuerySet', self.annotate(data_type=models.F('tag__data_type')))

    def with_name(self):
        return cast('TagValueQuerySet', self.annotate(name=models.F('tag__name')))


class TagValue(TimestampedModel):
    tag = models.ForeignKey('kims.Tag', on_delete=models.PROTECT, related_name="values")
    average = models.CharField(max_length=255)
    mean = models.CharField(max_length=255)
    date = models.DateTimeField()

    objects = TagValueQuerySet.as_manager()

    # metrics synced with K-IMS
    # when adding a new metric create a new field on the model with the same name
    metrics = ['mean', 'average']

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tag", "date"], name="unique_tag_value"),
            models.CheckConstraint(check=Q(date__minute=0, date__second=0), name="even_tag_value_date_hour"),
        ]

    def __str__(self) -> str:
        return f"Tag Value: {self.pk}"
