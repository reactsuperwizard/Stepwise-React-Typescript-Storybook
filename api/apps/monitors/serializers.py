from rest_framework import serializers

from apps.monitors.choices import MonitorElementDatasetType
from apps.monitors.models import Monitor, MonitorElement


class MonitorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = ('id', 'name', 'description', 'created_at', 'updated_at')


class MonitorElementDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorElement
        fields = ('id', 'name', 'description', 'value_unit', 'value_title')


class MonitorDetailsSerializer(serializers.ModelSerializer):
    elements = MonitorElementDetailsSerializer(many=True, source='public_elements')

    class Meta:
        model = Monitor
        fields = ('id', 'name', 'start_date', 'end_date', 'elements')


class MonitorElementDatasetSerializer(serializers.Serializer):
    date = serializers.DateField()
    baseline = serializers.FloatField(allow_null=True)
    target = serializers.FloatField(allow_null=True)
    current = serializers.FloatField(allow_null=True)


class MonitorElementDatasetListParamsSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=MonitorElementDatasetType.choices)
