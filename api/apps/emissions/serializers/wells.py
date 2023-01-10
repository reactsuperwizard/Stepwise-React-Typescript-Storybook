from rest_framework import serializers

from apps.emissions.models import (
    CompleteHelicopterUse,
    CompleteVesselUse,
    EmissionReductionInitiativeType,
    PlannedHelicopterUse,
    PlannedVesselUse,
    WellName,
)
from apps.wells.models import WellPlanner


class CreateUpdateWellSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellPlanner
        fields = (
            'name',
            'sidetrack',
            'description',
            'field',
            'location',
            'type',
            'asset',
            'fuel_type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'co2_tax',
            'nox_tax',
            'fuel_cost',
            'boilers_co2_per_fuel',
            'boilers_nox_per_fuel',
        )


class WellNameListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellName
        fields = (
            'id',
            'name',
        )


class CreateWellNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellName
        fields = ('name',)


class CreateUpdatePlannedVesselUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedVesselUse
        fields = (
            'vessel_type',
            'duration',
            'exposure_against_current_well',
            'waiting_on_weather',
            'season',
            'quota_obligation',
        )


class CreateUpdateCompleteVesselUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompleteVesselUse
        fields = (
            'vessel_type',
            'duration',
            'exposure_against_current_well',
            'waiting_on_weather',
            'season',
            'quota_obligation',
        )


class UpdateWellPlannedStartDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellPlanner
        fields = ('planned_start_date',)


class CreateUpdatePlannedHelicopterUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlannedHelicopterUse
        fields = ('helicopter_type', 'trips', 'trip_duration', 'exposure_against_current_well', 'quota_obligation')


class CreateUpdateCompleteHelicopterUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompleteHelicopterUse
        fields = ('helicopter_type', 'trips', 'trip_duration', 'exposure_against_current_well', 'quota_obligation')


class WellCO2EmissionSerializer(serializers.Serializer):
    date = serializers.DateField()
    asset = serializers.FloatField(source='total_asset')
    external_energy_supply = serializers.FloatField(source='total_external_energy_supply')
    vessels = serializers.FloatField(source='total_vessels')
    helicopters = serializers.FloatField(source='total_helicopters')
    materials = serializers.FloatField(source='total_materials')
    boilers = serializers.FloatField(source='total_boilers')


class WellEmissionReductionSerializer(serializers.Serializer):
    class EmissionReductionInitiativeSerializer(serializers.Serializer):
        id = serializers.IntegerField(source='emission_reduction_initiative')
        type = serializers.ChoiceField(
            choices=EmissionReductionInitiativeType.choices, source='emission_reduction_initiative__type'
        )
        name = serializers.CharField(source='emission_reduction_initiative__name')
        value = serializers.FloatField(source='total_value')

    date = serializers.DateField()
    emission_reduction_initiatives = EmissionReductionInitiativeSerializer(many=True)
