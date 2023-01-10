from rest_framework import serializers

from apps.emps.models import EMP, ConceptEMPElement, CustomEMPElement


class ConceptEMPElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptEMPElement
        fields = (
            'id',
            'name',
            'subarea',
            'percentage_improvement',
        )


class EMPSerializer(serializers.ModelSerializer):
    class CustomEMPElementSerializer(serializers.ModelSerializer):
        concept = ConceptEMPElementSerializer(source='concept_emp_element')

        class Meta:
            model = CustomEMPElement
            fields = (
                'id',
                'concept',
                'baseline_average',
                'target_average',
            )

    elements = CustomEMPElementSerializer(many=True)

    class Meta:
        model = EMP
        fields = (
            'id',
            'name',
            'description',
            'api_description',
            'start_date',
            'end_date',
            'total_rig_baseline_average',
            'total_rig_target_average',
            'elements',
        )


class CreateUpdateEMPSerializer(serializers.ModelSerializer):
    class CreateUpdateCustomEMPElementSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField(required=False, allow_null=True)
        concept_id = serializers.IntegerField()

        class Meta:
            model = CustomEMPElement
            fields = (
                'id',
                'concept_id',
                'baseline_average',
                'target_average',
            )

    elements = CreateUpdateCustomEMPElementSerializer(many=True)

    class Meta:
        model = EMP
        fields = (
            'name',
            'description',
            'api_description',
            'start_date',
            'end_date',
            'total_rig_baseline_average',
            'total_rig_target_average',
            'elements',
        )
