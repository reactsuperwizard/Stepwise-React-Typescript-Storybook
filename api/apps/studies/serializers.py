from django.db import models
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.projects.serializers import CustomRigSerializer
from apps.rigs.models import RigType
from apps.studies.models import (
    StudyElement,
    StudyElementDrillshipRelation,
    StudyElementJackupRigRelation,
    StudyElementSemiRigRelation,
    StudyMetric,
)


class StudyMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyMetric
        fields = ('id', 'name', 'unit', 'key', 'compatibility')


class StudyElementSerializer(serializers.ModelSerializer):
    class StudyElementRigSerializer(serializers.Serializer):
        id = serializers.IntegerField(source='rig.id')
        name = serializers.CharField(source='rig.name')
        type = serializers.SerializerMethodField()
        value = serializers.SerializerMethodField('get_element_value')

        def get_type(self, obj: models.Model) -> RigType:
            raise NotImplementedError

        def get_element_value(self, obj: models.Model) -> float | None:
            return getattr(obj.rig_plan_co2, obj.study_element.metric.key)  # type: ignore

    class StudyElementSemiRigSerializer(StudyElementRigSerializer):
        def get_type(self, obj: StudyElementSemiRigRelation) -> RigType:  # type: ignore[override]
            return RigType.SEMI

    class StudyElementJackupRigSerializer(StudyElementRigSerializer):
        def get_type(self, obj: StudyElementJackupRigRelation) -> RigType:  # type: ignore[override]
            return RigType.JACKUP

    class StudyElementDrillshipSerializer(StudyElementRigSerializer):
        value = serializers.FloatField(allow_null=True, help_text="Null value indicates ongoing calculations")  # type: ignore

        def get_type(self, obj: StudyElementDrillshipRelation) -> RigType:  # type: ignore[override]
            return RigType.DRILLSHIP

    rigs = serializers.SerializerMethodField()
    metric = StudyMetricSerializer()

    class Meta:
        model = StudyElement
        fields = (
            'id',
            'title',
            'metric',
            'plan',
            'project',
            'rigs',
            'order',
        )

    @extend_schema_field(StudyElementRigSerializer(many=True))
    def get_rigs(self, obj: StudyElement) -> list[dict]:
        return [
            *self.StudyElementSemiRigSerializer(obj.studyelementsemirigrelation_set.all(), many=True).data,
            *self.StudyElementJackupRigSerializer(obj.studyelementjackuprigrelation_set.all(), many=True).data,
            *self.StudyElementDrillshipSerializer(obj.studyelementdrillshiprelation_set.all(), many=True).data,
        ]


class StudyElementListSerializer(serializers.ModelSerializer):
    metric = StudyMetricSerializer()

    class Meta:
        model = StudyElement
        fields = (
            'id',
            'title',
            'metric',
            'plan',
            'project',
            'order',
        )


class CreateUpdateStudyElementSerializer(serializers.ModelSerializer):
    rigs = CustomRigSerializer(many=True)
    metric = serializers.SlugRelatedField(queryset=StudyMetric.objects.all(), slug_field='key')

    class Meta:
        model = StudyElement
        fields = ('title', 'plan', 'metric', 'rigs')


class SwapStudyElementsSerializer(serializers.Serializer):
    first_element = serializers.IntegerField()
    second_element = serializers.IntegerField()


class SwappedStudyElementsSerializer(serializers.Serializer):
    first_element = StudyElementListSerializer()
    second_element = StudyElementListSerializer()
