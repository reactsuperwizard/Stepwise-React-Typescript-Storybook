from typing import Any

from black import Dict
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.projects.models import ElementType, Plan, PlanWellRelation, Project
from apps.rigs.models import RigType
from apps.wells.models import CustomWell


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'description',
            'created_at',
            'updated_at',
        )


class CreateUpdateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'name',
            'description',
            'tugs_day_rate',
            'tugs_avg_move_fuel_consumption',
            'tugs_avg_transit_fuel_consumption',
            'tugs_move_speed',
            'tugs_transit_speed',
            'ahv_no_used',
            'ahv_no_days_per_location',
            'ahv_avg_fuel_consumption',
            'ahv_day_rate',
            'psv_calls_per_week',
            'psv_types',
            'psv_day_rate',
            'psv_avg_fuel_transit_consumption',
            'psv_avg_fuel_dp_consumption',
            'psv_speed',
            'psv_loading_time',
            'psv_fuel_price',
            'helicopter_no_flights_per_week',
            'helicopter_types',
            'helicopter_avg_fuel_consumption',
            'helicopter_rate_per_trip',
            'helicopter_fuel_price',
            'helicopter_cruise_speed',
            'marine_diesel_oil_price',
            'co2_tax',
            'nox_tax',
            'fuel_total_price',
            'fuel_density',
            'co2_emission_per_tonne_fuel',
            'co2_emission_per_m3_fuel',
        )


class ProjectDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'description',
            'tugs_day_rate',
            'tugs_avg_move_fuel_consumption',
            'tugs_avg_transit_fuel_consumption',
            'tugs_move_speed',
            'tugs_transit_speed',
            'ahv_no_used',
            'ahv_no_days_per_location',
            'ahv_avg_fuel_consumption',
            'ahv_day_rate',
            'psv_calls_per_week',
            'psv_types',
            'psv_day_rate',
            'psv_avg_fuel_transit_consumption',
            'psv_avg_fuel_dp_consumption',
            'psv_speed',
            'psv_fuel_price',
            'psv_loading_time',
            'helicopter_no_flights_per_week',
            'helicopter_types',
            'helicopter_avg_fuel_consumption',
            'helicopter_rate_per_trip',
            'helicopter_fuel_price',
            'helicopter_cruise_speed',
            'marine_diesel_oil_price',
            'co2_tax',
            'nox_tax',
            'fuel_total_price',
            'fuel_density',
            'co2_emission_per_tonne_fuel',
            'co2_emission_per_m3_fuel',
            'created_at',
            'updated_at',
        )


class PlanListSerializer(serializers.ModelSerializer):
    class PlanListWellSerializer(serializers.ModelSerializer):
        class Meta:
            model = CustomWell
            fields = (
                'id',
                'name',
            )

    wells = PlanListWellSerializer(many=True)

    class Meta:
        model = Plan
        fields = (
            'id',
            'name',
            'description',
            'created_at',
            'updated_at',
            'wells',
        )


class CustomRigSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=RigType.choices)


class PlanDetailsSerializer(serializers.ModelSerializer):
    class PlanDetailsWellSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField(source="well.pk")
        name = serializers.CharField(source="well.name")

        class Meta:
            model = PlanWellRelation
            fields = (
                'id',
                'name',
                'distance_from_previous_location',
                'distance_to_helicopter_base',
                'distance_to_psv_base',
                'distance_to_ahv_base',
                'distance_to_tug_base',
                'jackup_positioning_time',
                'semi_positioning_time',
                'operational_time',
            )

    wells = serializers.SerializerMethodField()
    reference_rig = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'name',
            'description',
            'block_name',
            'reference_rig',
            'distance_from_tug_base_to_previous_well',
            'created_at',
            'updated_at',
            'wells',
        )

    @extend_schema_field(PlanDetailsWellSerializer(many=True))
    def get_wells(self, obj: Plan) -> Dict[str, Any]:
        plan_wells = obj.plan_wells.order_by('order')
        return self.PlanDetailsWellSerializer(plan_wells, many=True).data

    @extend_schema_field(CustomRigSerializer)
    def get_reference_rig(self, obj: Plan) -> dict:
        if obj.reference_operation_jackup:
            return CustomRigSerializer(obj.reference_operation_jackup).data
        elif obj.reference_operation_semi:
            return CustomRigSerializer(obj.reference_operation_semi).data
        elif obj.reference_operation_drillship:
            return CustomRigSerializer(obj.reference_operation_drillship).data
        raise NotImplementedError('Missing reference rig')


class CreateUpdatePlanSerializer(serializers.ModelSerializer):
    class CreateUpdatePlanWellSerializer(serializers.ModelSerializer):
        id = serializers.IntegerField()

        class Meta:
            model = PlanWellRelation
            fields = (
                'id',
                'distance_from_previous_location',
                'distance_to_helicopter_base',
                'distance_to_psv_base',
                'distance_to_ahv_base',
                'distance_to_tug_base',
                'jackup_positioning_time',
                'semi_positioning_time',
                'operational_time',
            )

    wells = CreateUpdatePlanWellSerializer(many=True)
    reference_rig = CustomRigSerializer()

    class Meta:
        model = Plan

        fields = (
            'name',
            'description',
            'block_name',
            'reference_rig',
            'distance_from_tug_base_to_previous_well',
            'wells',
        )


class ElementListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.ChoiceField(choices=ElementType.choices, source='element_type')
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    project = serializers.IntegerField()
