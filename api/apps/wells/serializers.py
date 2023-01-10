from typing import Any, cast

from django.core.validators import MinValueValidator
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.api.serializers import DraftSerializer, IDSerializer
from apps.emissions.models import (
    Asset,
    Baseline,
    CompleteHelicopterUse,
    CompleteVesselUse,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    HelicopterType,
    MaterialType,
    PlannedHelicopterUse,
    PlannedVesselUse,
    VesselType,
    WellCompleteStepMaterial,
    WellName,
    WellPlannedStepMaterial,
)
from apps.wells.models import (
    ConceptWell,
    CustomWell,
    WellPlanner,
    WellPlannerCompleteStep,
    WellPlannerPlannedStep,
    WellReferenceMaterial,
)


class CustomWellListSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()

    class Meta:
        model = CustomWell
        fields = ('id', 'name', 'created_at', 'updated_at', 'draft', 'project')

    @extend_schema_field(IDSerializer(allow_null=True))
    def get_project(self, obj: CustomWell) -> dict | None:
        if obj.project:
            return IDSerializer(obj.project).data
        return None


class ConceptWellListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptWell
        fields = ('id', 'name', 'created_at', 'updated_at')


def UpdateCustomWellSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class UpdateCustomWellSerializer(DraftSerializer, serializers.ModelSerializer):
        class Meta:
            model = CustomWell
            fields = (
                'name',
                'type',
                'top_hole',
                'transport_section',
                'reservoir_section',
                'completion',
                'pna',
                'season',
                'water_depth',
                "metocean_data",
                "metocean_days_above_hs_5",
                "planned_time_per_well",
                "tvd_from_msl",
                "md_from_msl",
                "expected_reservoir_pressure",
                "expected_reservoir_temperature",
                "top_hole_section_hole_size",
                "surface_casing_section_hole_size",
                "intermediate_casing_section_hole_size",
                "production_casing_section_hole_size",
                "extension_section_hole_size",
                "intermediate_casing_section_mud_type",
                "production_casing_section_mud_type",
                "extension_section_mud_type",
                "intermediate_casing_section_mud_density",
                "production_casing_section_mud_density",
                "extension_section_mud_density",
                "conductor_size",
                "conductor_weight",
                "conductor_tvd_shoe_depth",
                "conductor_md_shoe_depth",
                "surface_casing_size",
                "surface_casing_weight",
                "surface_casing_tvd_shoe_depth",
                "surface_casing_md_shoe_depth",
                "intermediate_casing_size",
                "intermediate_casing_weight",
                "intermediate_casing_tvd_shoe_depth",
                "intermediate_casing_md_shoe_depth",
                "production_casing_size",
                "production_casing_weight",
                "production_casing_tvd_shoe_depth",
                "production_casing_md_shoe_depth",
                "liner_other_size",
                "liner_other_weight",
                "liner_other_tvd_shoe_depth",
                "liner_other_md_shoe_depth",
                "no_well_to_be_completed",
                "planned_time_per_completion_operation",
                "subsea_xmas_tree_size",
                "xt_weight",
                "lrp_size",
                "lrp_weight",
                "xt_running_tool_size",
                "xt_running_tool_weight",
                'draft',
            )
            extra_kwargs = {
                'name': {'allow_blank': draft, 'required': not draft},
                'type': {'allow_blank': draft, 'required': not draft},
                'top_hole': {'allow_blank': draft, 'required': not draft},
                'transport_section': {'allow_blank': draft, 'required': not draft},
                'reservoir_section': {'allow_blank': draft, 'required': not draft},
                'completion': {'allow_blank': draft, 'required': not draft},
                'pna': {'allow_blank': draft, 'required': not draft},
                'season': {'allow_blank': draft, 'required': not draft},
                'water_depth': {'allow_null': draft, 'required': not draft},
                'metocean_data': {'allow_blank': draft, 'required': not draft},
                'metocean_days_above_hs_5': {'allow_null': draft, 'required': not draft},
                'no_well_to_be_completed': {'allow_null': draft, 'required': not draft},
                'planned_time_per_completion_operation': {'allow_null': draft, 'required': not draft},
                'subsea_xmas_tree_size': {'allow_null': draft, 'required': not draft},
                'xt_weight': {'allow_null': draft, 'required': not draft},
                'lrp_size': {'allow_null': draft, 'required': not draft},
                'lrp_weight': {'allow_null': draft, 'required': not draft},
                'xt_running_tool_size': {'allow_null': draft, 'required': not draft},
                'xt_running_tool_weight': {'allow_null': draft, 'required': not draft},
            }

    return UpdateCustomWellSerializer


def CreateCustomWellSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class CreateCustomWellSerializer(UpdateCustomWellSerializerFactory(draft)):  # type: ignore
        project = serializers.IntegerField(required=False, allow_null=True)

        class Meta(UpdateCustomWellSerializerFactory(draft).Meta):  # type: ignore
            fields = UpdateCustomWellSerializerFactory(draft).Meta.fields + ('project',)  # type: ignore

    return CreateCustomWellSerializer


class CustomWellDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomWell
        fields = (
            'id',
            'name',
            'type',
            'top_hole',
            'transport_section',
            'reservoir_section',
            'completion',
            'pna',
            'season',
            'water_depth',
            "metocean_data",
            "metocean_days_above_hs_5",
            "planned_time_per_well",
            "tvd_from_msl",
            "md_from_msl",
            "expected_reservoir_pressure",
            "expected_reservoir_temperature",
            "top_hole_section_hole_size",
            "surface_casing_section_hole_size",
            "intermediate_casing_section_hole_size",
            "production_casing_section_hole_size",
            "extension_section_hole_size",
            "intermediate_casing_section_mud_type",
            "production_casing_section_mud_type",
            "extension_section_mud_type",
            "intermediate_casing_section_mud_density",
            "production_casing_section_mud_density",
            "extension_section_mud_density",
            "conductor_size",
            "conductor_weight",
            "conductor_tvd_shoe_depth",
            "conductor_md_shoe_depth",
            "surface_casing_size",
            "surface_casing_weight",
            "surface_casing_tvd_shoe_depth",
            "surface_casing_md_shoe_depth",
            "intermediate_casing_size",
            "intermediate_casing_weight",
            "intermediate_casing_tvd_shoe_depth",
            "intermediate_casing_md_shoe_depth",
            "production_casing_size",
            "production_casing_weight",
            "production_casing_tvd_shoe_depth",
            "production_casing_md_shoe_depth",
            "liner_other_size",
            "liner_other_weight",
            "liner_other_tvd_shoe_depth",
            "liner_other_md_shoe_depth",
            "no_well_to_be_completed",
            "planned_time_per_completion_operation",
            "subsea_xmas_tree_size",
            "xt_weight",
            "lrp_size",
            "lrp_weight",
            "xt_running_tool_size",
            "xt_running_tool_weight",
            'draft',
            'created_at',
            'updated_at',
        )


class ConceptWellDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptWell
        fields = (
            'id',
            'name',
            'type',
            'top_hole',
            'transport_section',
            'reservoir_section',
            'completion',
            'pna',
            'season',
            'water_depth',
            "metocean_data",
            "metocean_days_above_hs_5",
            "planned_time_per_well",
            "tvd_from_msl",
            "md_from_msl",
            "expected_reservoir_pressure",
            "expected_reservoir_temperature",
            "top_hole_section_hole_size",
            "surface_casing_section_hole_size",
            "intermediate_casing_section_hole_size",
            "production_casing_section_hole_size",
            "extension_section_hole_size",
            "intermediate_casing_section_mud_type",
            "production_casing_section_mud_type",
            "extension_section_mud_type",
            "intermediate_casing_section_mud_density",
            "production_casing_section_mud_density",
            "extension_section_mud_density",
            "conductor_size",
            "conductor_weight",
            "conductor_tvd_shoe_depth",
            "conductor_md_shoe_depth",
            "surface_casing_size",
            "surface_casing_weight",
            "surface_casing_tvd_shoe_depth",
            "surface_casing_md_shoe_depth",
            "intermediate_casing_size",
            "intermediate_casing_weight",
            "intermediate_casing_tvd_shoe_depth",
            "intermediate_casing_md_shoe_depth",
            "production_casing_size",
            "production_casing_weight",
            "production_casing_tvd_shoe_depth",
            "production_casing_md_shoe_depth",
            "liner_other_size",
            "liner_other_weight",
            "liner_other_tvd_shoe_depth",
            "liner_other_md_shoe_depth",
            "no_well_to_be_completed",
            "planned_time_per_completion_operation",
            "subsea_xmas_tree_size",
            "xt_weight",
            "lrp_size",
            "lrp_weight",
            "xt_running_tool_size",
            "xt_running_tool_weight",
            'created_at',
            'updated_at',
        )


class WellPlannerPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPhase
        fields = (
            'id',
            'name',
            'color',
        )


class WellPlannerModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomMode
        fields = (
            'id',
            'name',
        )


class WellPlannerVesselTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselType
        fields = ('id', 'type')


class WellPlannerHelicopterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelicopterType
        fields = ('id', 'type')


def WellStepMaterialSerializerFactory(
    WellStepMaterialModel: type[WellPlannedStepMaterial] | type[WellCompleteStepMaterial],
) -> type[serializers.ModelSerializer]:
    class WellStepMaterialSerializer(serializers.ModelSerializer):
        class WellStepMaterialTypeSerializer(serializers.ModelSerializer):
            class Meta:
                model = MaterialType
                fields = ('id', 'category', 'unit')

        material_type = WellStepMaterialTypeSerializer()

        class Meta:
            model = WellStepMaterialModel
            fields = (
                'id',
                'material_type',
                'quantity',
                'quota',
            )

    return WellStepMaterialSerializer


WellPlannedStepMaterialSerializer = WellStepMaterialSerializerFactory(WellPlannedStepMaterial)
WellCompleteStepMaterialSerializer = WellStepMaterialSerializerFactory(WellCompleteStepMaterial)


class WellPlannerDetailsSerializer(serializers.ModelSerializer):
    class WellNameSerializer(serializers.ModelSerializer):
        class Meta:
            model = WellName
            fields = ('id', 'name')

    class PlannedVesselUseListSerializer(serializers.ModelSerializer):
        vessel_type = WellPlannerVesselTypeSerializer()

        class Meta:
            model = PlannedVesselUse
            fields = (
                'id',
                'vessel_type',
                'duration',
                'exposure_against_current_well',
                'waiting_on_weather',
                'season',
                'quota_obligation',
            )

    class CompleteVesselUseListSerializer(serializers.ModelSerializer):
        vessel_type = WellPlannerVesselTypeSerializer()

        class Meta:
            model = CompleteVesselUse
            fields = (
                'id',
                'vessel_type',
                'duration',
                'exposure_against_current_well',
                'waiting_on_weather',
                'season',
                'quota_obligation',
                'approved',
            )

    class PlannedHelicopterUseListSerializer(serializers.ModelSerializer):
        helicopter_type = WellPlannerHelicopterTypeSerializer()

        class Meta:
            model = PlannedHelicopterUse
            fields = (
                'id',
                'helicopter_type',
                'trips',
                'trip_duration',
                'exposure_against_current_well',
                'quota_obligation',
            )

    class CompleteHelicopterUseListSerializer(serializers.ModelSerializer):
        helicopter_type = WellPlannerHelicopterTypeSerializer()

        class Meta:
            model = CompleteHelicopterUse
            fields = (
                'id',
                'helicopter_type',
                'trips',
                'trip_duration',
                'exposure_against_current_well',
                'quota_obligation',
                'approved',
            )

    class WellPlannerDetailsPlannedStepSerializer(serializers.ModelSerializer):
        emission_reduction_initiatives = serializers.PrimaryKeyRelatedField(many=True, read_only=True)  # type: ignore
        phase = WellPlannerPhaseSerializer()
        mode = WellPlannerModeSerializer()
        materials = WellPlannedStepMaterialSerializer(many=True)

        class Meta:
            model = WellPlannerPlannedStep
            fields = (
                "id",
                "order",
                "phase",
                "mode",
                "duration",
                "waiting_on_weather",
                "improved_duration",
                "season",
                "carbon_capture_storage_system_quantity",
                "well_section_length",
                "emission_reduction_initiatives",
                "comment",
                "external_energy_supply_enabled",
                "external_energy_supply_quota",
                "materials",
            )

    class WellPlannerDetailsCompleteStepSerializer(serializers.ModelSerializer):
        emission_reduction_initiatives = serializers.PrimaryKeyRelatedField(many=True, read_only=True)  # type: ignore
        phase = WellPlannerPhaseSerializer()
        mode = WellPlannerModeSerializer()
        materials = WellCompleteStepMaterialSerializer(many=True)

        class Meta:
            model = WellPlannerCompleteStep
            fields = (
                "id",
                "order",
                "phase",
                "mode",
                "duration",
                "waiting_on_weather",
                "season",
                "carbon_capture_storage_system_quantity",
                "emission_reduction_initiatives",
                "well_section_length",
                "comment",
                "external_energy_supply_enabled",
                "external_energy_supply_quota",
                "materials",
                "approved",
            )

    class WellPlannerAssetSerializer(serializers.ModelSerializer):
        class Meta:
            model = Asset
            fields = (
                "id",
                "name",
            )

    class WellPlannerBaselineSerializer(serializers.ModelSerializer):
        class Meta:
            model = Baseline
            fields = (
                "id",
                "name",
            )

    class WellPlannerEmissionManagementPlanSerializer(serializers.ModelSerializer):
        class Meta:
            model = EmissionManagementPlan
            fields = (
                "id",
                "name",
            )

    name = WellNameSerializer()
    asset = WellPlannerAssetSerializer()
    baseline = WellPlannerBaselineSerializer()
    emission_management_plan = WellPlannerEmissionManagementPlanSerializer(allow_null=True)

    planned_vessel_uses = PlannedVesselUseListSerializer(many=True, source='plannedvesseluse_set')
    complete_vessel_uses = CompleteVesselUseListSerializer(many=True, source='completevesseluse_set')

    planned_helicopter_uses = PlannedHelicopterUseListSerializer(many=True, source='plannedhelicopteruse_set')
    complete_helicopter_uses = CompleteHelicopterUseListSerializer(many=True, source='completehelicopteruse_set')

    planned_steps = WellPlannerDetailsPlannedStepSerializer(many=True)
    complete_steps = WellPlannerDetailsCompleteStepSerializer(many=True)

    class Meta:
        model = WellPlanner
        fields = (
            'id',
            'name',
            'sidetrack',
            'description',
            'field',
            'location',
            'type',
            'asset',
            'baseline',
            'emission_management_plan',
            'fuel_type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'co2_tax',
            'nox_tax',
            'fuel_cost',
            'boilers_co2_per_fuel',
            'boilers_nox_per_fuel',
            'planned_start_date',
            'actual_start_date',
            'current_step',
            'planned_vessel_uses',
            'complete_vessel_uses',
            'planned_helicopter_uses',
            'complete_helicopter_uses',
            'planned_steps',
            'complete_steps',
        )

    def __init__(self, instance: WellPlanner | None = None, **kwargs: Any):
        super().__init__(instance=self.get_ordered_instance(instance) if instance else None, **kwargs)

    def get_ordered_instance(self, well_planner: WellPlanner) -> WellPlanner:
        return cast(
            WellPlanner,
            (
                WellPlanner.objects.select_related('asset', 'name', 'baseline', 'emission_management_plan')
                .prefetch_related(
                    Prefetch(
                        'planned_steps',
                        queryset=WellPlannerPlannedStep.objects.prefetch_related(
                            'emission_reduction_initiatives',
                            Prefetch(
                                'materials', queryset=WellPlannedStepMaterial.objects.select_related('material_type')
                            ),
                        ).order_by('order'),
                    ),
                    Prefetch(
                        'complete_steps',
                        queryset=WellPlannerCompleteStep.objects.prefetch_related(
                            'emission_reduction_initiatives',
                            Prefetch(
                                'materials', queryset=WellCompleteStepMaterial.objects.select_related('material_type')
                            ),
                        ).order_by('order'),
                    ),
                    Prefetch(
                        'plannedvesseluse_set',
                        queryset=PlannedVesselUse.objects.select_related('vessel_type').order_by('id'),
                    ),
                    Prefetch(
                        'completevesseluse_set',
                        queryset=CompleteVesselUse.objects.select_related('vessel_type').order_by('id'),
                    ),
                    Prefetch(
                        'plannedhelicopteruse_set',
                        queryset=PlannedHelicopterUse.objects.select_related('helicopter_type').order_by('id'),
                    ),
                    Prefetch(
                        'completehelicopteruse_set',
                        queryset=CompleteHelicopterUse.objects.select_related('helicopter_type').order_by('id'),
                    ),
                )
                .get(pk=well_planner.pk)
            ),
        )


def CreateWellStepSerializerFactory(
    WellStepModel: type[WellPlannerPlannedStep] | type[WellPlannerCompleteStep],
    WellStepMaterialModel: type[WellPlannedStepMaterial] | type[WellCompleteStepMaterial],
) -> type[serializers.ModelSerializer]:
    class CreateWellStepSerializer(serializers.ModelSerializer):
        class CreateWellStepMaterialSerializer(serializers.ModelSerializer):
            class Meta:
                model = WellStepMaterialModel
                fields = (
                    'material_type',
                    'quantity',
                    'quota',
                )

        materials = CreateWellStepMaterialSerializer(many=True)

        class Meta:
            model = WellStepModel
            fields = (
                "phase",
                "duration",
                "mode",
                "season",
                "waiting_on_weather",
                "carbon_capture_storage_system_quantity",
                "emission_reduction_initiatives",
                "well_section_length",
                "comment",
                "external_energy_supply_enabled",
                "external_energy_supply_quota",
                "materials",
            )

    return CreateWellStepSerializer


def UpdateWellStepSerializerFactory(
    WellStepModel: type[WellPlannerPlannedStep] | type[WellPlannerCompleteStep],
    WellStepMaterialModel: type[WellPlannedStepMaterial] | type[WellCompleteStepMaterial],
) -> type[serializers.ModelSerializer]:
    class UpdateWellStepSerializer(serializers.ModelSerializer):
        class UpdateWellStepMaterialSerializer(serializers.ModelSerializer):
            id = serializers.IntegerField(required=False, allow_null=True)

            class Meta:
                model = WellStepMaterialModel
                fields = (
                    'id',
                    'material_type',
                    'quantity',
                    'quota',
                )

        materials = UpdateWellStepMaterialSerializer(many=True)

        class Meta:
            model = WellStepModel
            fields = (
                "phase",
                "duration",
                "mode",
                "season",
                "waiting_on_weather",
                "carbon_capture_storage_system_quantity",
                "emission_reduction_initiatives",
                "well_section_length",
                "comment",
                "external_energy_supply_enabled",
                "external_energy_supply_quota",
                "materials",
            )

    return UpdateWellStepSerializer


CreateWellPlannerPlannedStepSerializer = CreateWellStepSerializerFactory(
    WellPlannerPlannedStep, WellPlannedStepMaterial
)
UpdateWellPlannerPlannedStepSerializer = UpdateWellStepSerializerFactory(
    WellPlannerPlannedStep, WellPlannedStepMaterial
)
CreateWellPlannerCompleteStepSerializer = CreateWellStepSerializerFactory(
    WellPlannerCompleteStep, WellCompleteStepMaterial
)
UpdateWellPlannerCompleteStepSerializer = UpdateWellStepSerializerFactory(
    WellPlannerCompleteStep, WellCompleteStepMaterial
)


class WellPlannerCO2EmissionReductionInitiativeSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='emission_reduction_initiative.pk')
    value = serializers.FloatField()


class WellPlannerCO2DatasetSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    phase = WellPlannerPhaseSerializer(source='step.phase')
    mode = WellPlannerModeSerializer(source='step.mode')
    step = IDSerializer()
    rig = serializers.FloatField()
    vessels = serializers.FloatField()
    helicopters = serializers.FloatField()
    external_energy_supply = serializers.FloatField()
    cement = serializers.FloatField()
    steel = serializers.FloatField()
    emission_reduction_initiatives = WellPlannerCO2EmissionReductionInitiativeSerializer(many=True)


class WellPlannerCO2SavedDatasetSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    rig = serializers.FloatField()
    vessels = serializers.FloatField()
    helicopters = serializers.FloatField()
    external_energy_supply = serializers.FloatField()
    cement = serializers.FloatField()
    steel = serializers.FloatField()
    emission_reduction_initiatives = WellPlannerCO2EmissionReductionInitiativeSerializer(many=True)


class WellPlannerSummarySerializer(serializers.Serializer):
    total_baseline = serializers.FloatField()
    total_target = serializers.FloatField()
    total_improved_duration = serializers.FloatField()


class WellPlannerCompleteSummarySerializer(serializers.Serializer):
    total_baseline = serializers.FloatField()
    total_target = serializers.FloatField()
    total_duration = serializers.FloatField()


class WellPlannerMeasurementDatasetSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    value = serializers.FloatField()


class UpdateWellPlannerEmissionReductionInitiativesSerializer(serializers.Serializer):
    emission_reduction_initiatives = serializers.PrimaryKeyRelatedField(
        many=True, queryset=EmissionReductionInitiative.objects.live()
    )


class MoveWellPlannerStepSerializer(serializers.Serializer):
    order = serializers.IntegerField(validators=[MinValueValidator(0)])


class WellReferenceMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = WellReferenceMaterial
        fields = ('id', 'details', 'vehicles', 'planning', 'complete')


class WellPlannerPlannedStepCO2Serializer(serializers.Serializer):
    baseline = serializers.FloatField()
    target = serializers.FloatField()
    rig = serializers.FloatField()
    vessels = serializers.FloatField()
    helicopters = serializers.FloatField()
    external_energy_supply = serializers.FloatField()
    cement = serializers.FloatField()
    steel = serializers.FloatField()
    emission_reduction_initiatives = WellPlannerCO2EmissionReductionInitiativeSerializer(many=True)


class ApproveWellPlannerCompleteStepsSerializer(serializers.Serializer):
    complete_steps = serializers.PrimaryKeyRelatedField(many=True, queryset=WellPlannerCompleteStep.objects.all())


class ApproveWellPlannerCompleteHelicopterUsesSerializer(serializers.Serializer):
    complete_helicopter_uses = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CompleteHelicopterUse.objects.all()
    )


class ApproveWellPlannerCompleteVesselUsesSerializer(serializers.Serializer):
    complete_vessel_uses = serializers.PrimaryKeyRelatedField(many=True, queryset=CompleteVesselUse.objects.all())


class StartEndDateParametersSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)


class UpdateWellPlannerActualStartDateSerializer(serializers.Serializer):
    actual_start_date = serializers.DateField()


class WellPlannerListSerializer(serializers.ModelSerializer):
    class WellPlannerListAssetSerializer(serializers.ModelSerializer):
        class Meta:
            model = Asset
            fields = (
                'id',
                'name',
            )

    class WellNameSerializer(serializers.ModelSerializer):
        class Meta:
            model = WellName
            fields = (
                'id',
                'name',
            )

    name = WellNameSerializer()
    asset = WellPlannerListAssetSerializer()
    baseline = IDSerializer()

    class Meta:
        model = WellPlanner
        fields = (
            'id',
            'name',
            'sidetrack',
            'asset',
            'field',
            'location',
            'description',
            'type',
            'planned_start_date',
            'actual_start_date',
            'current_step',
            'baseline',
        )


class WellPlannerPhaseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomPhase
        fields = (
            'id',
            'name',
            'color',
            'transit',
        )


class WellPlannerModeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomMode
        fields = (
            'id',
            'name',
            'transit',
        )
