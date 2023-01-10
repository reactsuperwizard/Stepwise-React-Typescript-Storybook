from django.db import models
from ordered_model.models import OrderedModel

from apps.core.models import TimestampedModel
from apps.projects.models import Project
from apps.rigs.models import RigType


class Study(Project):
    # used only in haystack to index Study and Project separately

    class Meta:
        proxy = True


class StudyMetric(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Display name of the metric")
    key = models.CharField(max_length=100, unique=True, help_text="Rig CO2 plan attribute field name")
    unit = models.CharField(max_length=20, blank=True)

    is_jackup_compatible = models.BooleanField()
    is_semi_compatible = models.BooleanField()
    is_drillship_compatible = models.BooleanField()

    def __str__(self):
        return f'Study Metric: {self.name}'

    @property
    def compatibility(self) -> list[RigType]:
        return list(
            filter(
                None,
                [
                    RigType.JACKUP if self.is_jackup_compatible else None,
                    RigType.SEMI if self.is_semi_compatible else None,
                    RigType.DRILLSHIP if self.is_drillship_compatible else None,
                ],
            )
        )


class AbstractStudyElementRigRelation(models.Model):
    study_element = models.ForeignKey("studies.StudyElement", on_delete=models.CASCADE)
    # todo: remove once we implemented calculators for all rig types
    value = models.FloatField(null=True)

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(fields=["study_element", "rig"], name="unique_%(app_label)s_%(class)s")]


class StudyElementSemiRigRelation(AbstractStudyElementRigRelation):
    rig = models.ForeignKey("rigs.CustomSemiRig", on_delete=models.CASCADE)
    rig_plan_co2 = models.ForeignKey('rigs.CustomSemiPlanCO2', on_delete=models.CASCADE)

    def __str__(self):
        return f"Study Element Semi Rig Relation: {self.pk}"


class StudyElementJackupRigRelation(AbstractStudyElementRigRelation):
    rig = models.ForeignKey("rigs.CustomJackupRig", on_delete=models.CASCADE)
    rig_plan_co2 = models.ForeignKey('rigs.CustomJackupPlanCO2', on_delete=models.CASCADE)

    def __str__(self):
        return f"Study Element Jackup Rig Relation: {self.pk}"


class StudyElementDrillshipRelation(AbstractStudyElementRigRelation):
    rig = models.ForeignKey("rigs.CustomDrillship", on_delete=models.CASCADE)

    def __str__(self):
        return f"Study Element Drillship Relation: {self.pk}"


class StudyElement(OrderedModel, TimestampedModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='study_elements')
    title = models.CharField(max_length=255)
    metric = models.ForeignKey(StudyMetric, on_delete=models.PROTECT)
    plan = models.ForeignKey('projects.Plan', on_delete=models.CASCADE, related_name="study_elements")
    semi_rigs = models.ManyToManyField(
        "rigs.CustomSemiRig", blank=True, through=StudyElementSemiRigRelation, related_name="study_elements"
    )
    jackup_rigs = models.ManyToManyField(
        "rigs.CustomJackupRig", blank=True, through=StudyElementJackupRigRelation, related_name="study_elements"
    )
    drillships = models.ManyToManyField("rigs.CustomDrillship", blank=True, through=StudyElementDrillshipRelation)
    creator = models.ForeignKey('tenants.User', on_delete=models.PROTECT)
    order_with_respect_to = 'project'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "order"], name="unique_study_element_order", deferrable=models.Deferrable.DEFERRED
            ),
        ]

    def __str__(self):
        return f'Study Element: {self.pk}'
