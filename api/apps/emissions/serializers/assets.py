from typing import Any, cast

from django.db.models import OuterRef, Prefetch, Subquery
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.core.api.serializers import IDSerializer
from apps.emissions.models import (
    Asset,
    AssetReferenceMaterial,
    AssetSeason,
    Baseline,
    BaselineInput,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    EmissionReductionInitiativeInput,
    ExternalEnergySupply,
    HelicopterType,
    MaterialType,
    VesselType,
)


class AssetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = (
            'id',
            'name',
            'type',
            'green_house_gas_class_notation',
            'design_description',
            'draft',
        )


class CompleteAssetListSerializer(serializers.ModelSerializer):
    active_baseline = serializers.CharField()
    active_emission_management_plan = serializers.CharField(allow_null=True)

    class Meta:
        model = Asset
        fields = ('id', 'name', 'type', 'active_baseline', 'active_emission_management_plan')


class AssetExternalEnergySupplySerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "type",
            "capacity",
            "co2",
            "nox",
            "generator_efficiency_factor",
        )
        model = ExternalEnergySupply


class CreateAssetSerializer(serializers.ModelSerializer):
    external_energy_supply = AssetExternalEnergySupplySerializer()

    class Meta:
        model = Asset
        fields = (
            'name',
            'type',
            'green_house_gas_class_notation',
            'design_description',
            'external_energy_supply',
        )


class UpdateAssetSerializer(serializers.ModelSerializer):
    external_energy_supply = AssetExternalEnergySupplySerializer()

    class Meta:
        model = Asset
        fields = (
            'name',
            'type',
            'green_house_gas_class_notation',
            'design_description',
            'draft',
            'external_energy_supply',
        )


class BaselineDetailsSerializer(serializers.ModelSerializer):
    class BaselineDetailsSeasonSerializer(serializers.Serializer):
        class BaselineDetailsInputSerializer(serializers.ModelSerializer):
            phase = IDSerializer()
            mode = IDSerializer()

            class Meta:
                model = BaselineInput
                fields = (
                    'id',
                    'order',
                    'phase',
                    'mode',
                    'value',
                )

        inputs = BaselineDetailsInputSerializer(many=True)
        transit = serializers.FloatField(min_value=0)

    asset = IDSerializer()
    summer = serializers.SerializerMethodField()
    winter = serializers.SerializerMethodField()

    class Meta:
        model = Baseline
        fields = (
            'id',
            'asset',
            'name',
            'description',
            'boilers_fuel_consumption_summer',
            'boilers_fuel_consumption_winter',
            'draft',
            'summer',
            'winter',
            'is_used',
            'updated_at',
        )

    def __init__(self, instance: Baseline | None = None, **kwargs: Any):
        super().__init__(instance=self.get_instance(instance) if instance else None, **kwargs)

    def get_instance(self, baseline: Baseline) -> Baseline:
        return cast(
            Baseline,
            Baseline.objects.prefetch_related(
                Prefetch(
                    'baselineinput_set',
                    queryset=BaselineInput.objects.inputs()
                    .filter(season=AssetSeason.SUMMER)
                    .select_related('phase', 'mode')
                    .order_by('order'),
                    to_attr='summer_inputs',
                ),
                Prefetch(
                    'baselineinput_set',
                    queryset=BaselineInput.objects.inputs()
                    .filter(
                        season=AssetSeason.WINTER,
                    )
                    .select_related('phase', 'mode')
                    .order_by('order'),
                    to_attr='winter_inputs',
                ),
            ).get(pk=baseline.pk),
        )

    @extend_schema_field(BaselineDetailsSeasonSerializer)
    def get_summer(self, baseline: Baseline) -> dict:
        summer_transit_input = BaselineInput.objects.transit().get(
            baseline=baseline,
            season=AssetSeason.SUMMER,
        )
        return self.BaselineDetailsSeasonSerializer(
            {'inputs': baseline.summer_inputs, 'transit': summer_transit_input.value}  # type: ignore
        ).data

    @extend_schema_field(BaselineDetailsSeasonSerializer)
    def get_winter(self, baseline: Baseline) -> dict:
        winter_transit_input = BaselineInput.objects.transit().get(
            baseline=baseline,
            season=AssetSeason.WINTER,
        )
        return self.BaselineDetailsSeasonSerializer(
            {
                'inputs': baseline.winter_inputs,  # type: ignore
                'transit': winter_transit_input.value,
            }
        ).data


class AssetDetailsSerializer(serializers.ModelSerializer):
    class BaselineSerializer(serializers.ModelSerializer):
        class Meta:
            model = Baseline
            fields = (
                'id',
                'name',
                'description',
                'updated_at',
                'active',
                'draft',
            )

    class EmissionManagementPlanSerializer(serializers.ModelSerializer):
        class Meta:
            model = EmissionManagementPlan
            fields = (
                'id',
                'name',
                'updated_at',
                'description',
                'version',
                'draft',
                'active',
            )

    class ExternalEnergySupplySerializer(serializers.ModelSerializer):
        class Meta:
            fields = (
                "type",
                "capacity",
                "co2",
                "nox",
                "generator_efficiency_factor",
            )
            model = ExternalEnergySupply

    baselines = BaselineSerializer(many=True, source='live_baselines')
    emission_management_plans = serializers.SerializerMethodField()
    external_energy_supply = ExternalEnergySupplySerializer()

    class Meta:
        model = Asset
        fields = (
            'id',
            'name',
            'type',
            'green_house_gas_class_notation',
            'design_description',
            'draft',
            'baselines',
            'emission_management_plans',
            'external_energy_supply',
        )

    def __init__(self, instance: Asset | None = None, **kwargs: Any):
        super().__init__(instance=self.get_instance(instance) if instance else instance, **kwargs)

    def get_instance(self, asset: Asset) -> Asset:
        return cast(
            Asset,
            Asset.objects.select_related('external_energy_supply')
            .prefetch_related(
                Prefetch(
                    'baselines',
                    queryset=Baseline.objects.live().order_by('created_at'),
                    to_attr='live_baselines',
                ),
            )
            .get(pk=asset.pk),
        )

    @extend_schema_field(EmissionManagementPlanSerializer(many=True))
    def get_emission_management_plans(self, obj: Asset) -> ReturnDict:
        active_baseline = obj.baselines.filter(active=True).first()

        if not active_baseline:
            emission_management_plans = EmissionManagementPlan.objects.none()
        else:
            emission_management_plans = active_baseline.emission_management_plans.live().order_by('id')

        return self.EmissionManagementPlanSerializer(emission_management_plans, many=True).data


class AssetReferenceMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetReferenceMaterial
        fields = ('id', 'details', 'baseline', 'emp')


class AssetPhaseSerializer(serializers.ModelSerializer):
    custom = serializers.SerializerMethodField()

    class Meta:
        model = CustomPhase
        fields = ('id', 'name', 'description', 'custom')

    def get_custom(self, obj: CustomPhase) -> bool:
        return obj.phase_id is None


class AssetModeSerializer(serializers.ModelSerializer):
    custom = serializers.SerializerMethodField()

    class Meta:
        model = CustomMode
        fields = ('id', 'name', 'description', 'custom')

    def get_custom(self, obj: CustomMode) -> bool:
        return obj.mode_id is None


class CreateUpdateCustomPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPhase
        fields = ('name', 'description')


class CreateUpdateCustomModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomMode
        fields = ('name', 'description')


class CreateUpdateBaselineSerializer(serializers.ModelSerializer):
    class CreateUpdateBaselineSeasonSerializer(serializers.Serializer):
        class CreateUpdateBaselineSeasonInputSerializer(serializers.ModelSerializer):
            phase = serializers.PrimaryKeyRelatedField(queryset=CustomPhase.objects.exclude(phase__transit=True))
            mode = serializers.PrimaryKeyRelatedField(queryset=CustomMode.objects.exclude(mode__transit=True))

            class Meta:
                model = BaselineInput
                fields = ('phase', 'mode', 'value')

        transit = serializers.FloatField(min_value=0)
        inputs = CreateUpdateBaselineSeasonInputSerializer(many=True)

    summer = CreateUpdateBaselineSeasonSerializer()
    winter = CreateUpdateBaselineSeasonSerializer()

    class Meta:
        model = Baseline
        fields = (
            'name',
            'description',
            'draft',
            'boilers_fuel_consumption_summer',
            'boilers_fuel_consumption_winter',
            'summer',
            'winter',
        )


class EmissionReductionInitiativeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionReductionInitiative
        fields = ('id', 'name', 'type')


class VesselTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselType
        fields = (
            'id',
            'type',
            'fuel_type',
            'fuel_density',
            'fuel_consumption_summer',
            'fuel_consumption_winter',
            'co2_per_fuel',
            'nox_per_fuel',
            'co2_tax',
            'nox_tax',
            'fuel_cost',
        )


class AllVesselTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselType
        fields = (
            'id',
            'type',
        )


class CreateUpdateVesselTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselType
        fields = (
            'type',
            'fuel_type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'co2_tax',
            'nox_tax',
            'fuel_cost',
            'fuel_consumption_summer',
            'fuel_consumption_winter',
        )


class EmissionReductionInitiativeDetailsSerializer(serializers.ModelSerializer):
    class EmissionReductionInitiativeDetailInputSerializer(serializers.ModelSerializer):
        phase = IDSerializer()
        mode = IDSerializer()

        class Meta:
            model = EmissionReductionInitiativeInput
            fields = (
                'id',
                'phase',
                'mode',
                'value',
            )

    inputs = EmissionReductionInitiativeDetailInputSerializer(many=True)
    transit = serializers.SerializerMethodField()

    class Meta:
        model = EmissionReductionInitiative
        fields = ('id', 'name', 'type', 'description', 'vendor', 'deployment_date', 'inputs', 'transit')

    def __init__(self, instance: EmissionReductionInitiative | None = None, **kwargs: Any):
        super().__init__(instance=self.get_instance(instance) if instance else instance, **kwargs)

    def get_instance(self, emission_reduction_initiative: EmissionReductionInitiative) -> EmissionReductionInitiative:
        return cast(
            EmissionReductionInitiative,
            EmissionReductionInitiative.objects.prefetch_related(
                Prefetch(
                    'emission_reduction_initiative_inputs',
                    queryset=EmissionReductionInitiativeInput.objects.inputs()
                    .select_related('phase', 'mode')
                    .order_by('pk'),
                    to_attr='inputs',
                ),
            )
            .annotate(
                transit=Subquery(
                    EmissionReductionInitiativeInput.objects.transit()
                    .filter(
                        emission_reduction_initiative=OuterRef('pk'),
                    )
                    .values('value')[:1]
                )
            )
            .get(pk=emission_reduction_initiative.pk),
        )

    def get_transit(self, obj: EmissionReductionInitiative) -> float:
        return obj.transit or 0.0  # type: ignore


class CreateUpdateEmissionReductionInitiativeSerializer(serializers.ModelSerializer):
    class CreateUpdateEmissionReductionInitiativeInputSerializer(serializers.ModelSerializer):
        phase = serializers.PrimaryKeyRelatedField(queryset=CustomPhase.objects.exclude(phase__transit=True))
        mode = serializers.PrimaryKeyRelatedField(queryset=CustomMode.objects.exclude(mode__transit=True))

        class Meta:
            model = EmissionReductionInitiativeInput
            fields = ('phase', 'mode', 'value')

    inputs = CreateUpdateEmissionReductionInitiativeInputSerializer(many=True)
    transit = serializers.FloatField(min_value=0)

    class Meta:
        model = EmissionReductionInitiative
        fields = ('name', 'type', 'description', 'vendor', 'deployment_date', 'inputs', 'transit')


class EmissionManagementPlanDetailsSerializer(serializers.ModelSerializer):
    class EmissionManagementPlanDetailsInitiativeSerializer(serializers.ModelSerializer):
        class Meta:
            model = EmissionReductionInitiative
            fields = ('id', 'name', 'description', 'type', 'vendor', 'deployment_date')

    initiatives = EmissionManagementPlanDetailsInitiativeSerializer(
        many=True, source='live_emission_reduction_initiatives'
    )

    class Meta:
        model = EmissionManagementPlan
        fields = (
            'id',
            'name',
            'description',
            'version',
            'updated_at',
            'draft',
            'initiatives',
        )

    def __init__(self, instance: EmissionManagementPlan | None = None, **kwargs: Any):
        super().__init__(instance=self.get_instance(instance) if instance else instance, **kwargs)

    def get_instance(self, emission_management_plan: EmissionManagementPlan) -> EmissionManagementPlan:
        return cast(
            EmissionManagementPlan,
            EmissionManagementPlan.objects.prefetch_related(
                Prefetch(
                    'emission_reduction_initiatives',
                    queryset=EmissionReductionInitiative.objects.live(),
                    to_attr='live_emission_reduction_initiatives',
                )
            ).get(pk=emission_management_plan.pk),
        )


class CreateUpdateEmissionManagementPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionManagementPlan
        fields = ('name', 'description', 'version', 'draft')


class HelicopterTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelicopterType
        fields = (
            'id',
            'type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'fuel_consumption',
            'fuel_cost',
            'co2_tax',
            'nox_tax',
        )


class CreateUpdateHelicopterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelicopterType
        fields = (
            'type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'fuel_consumption',
            'fuel_cost',
            'co2_tax',
            'nox_tax',
        )


class AllHelicopterTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelicopterType
        fields = (
            'id',
            'type',
        )


class MaterialTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = (
            'id',
            'type',
            'category',
            'unit',
            'co2',
        )


class AllMaterialTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = (
            'id',
            'type',
            'category',
            'unit',
        )


class BaselineModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomMode
        fields = ('id', 'name')


class BaselinePhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPhase
        fields = (
            'id',
            'name',
        )


class CreateMaterialTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = (
            'type',
            'category',
            'unit',
            'co2',
        )


class UpdateMaterialTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = (
            'type',
            'unit',
            'co2',
        )
