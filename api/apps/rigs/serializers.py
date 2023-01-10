from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.api.serializers import DraftSerializer
from apps.rigs.models import (
    ConceptDrillship,
    ConceptJackupRig,
    ConceptSemiRig,
    CustomDrillship,
    CustomJackupRig,
    CustomSemiRig,
    RigType,
)


class CustomRigListProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class CustomRigListEMPSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class CustomRigListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.ChoiceField(choices=RigType.choices)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    draft = serializers.BooleanField()
    project = serializers.SerializerMethodField()
    emp = serializers.SerializerMethodField()

    @extend_schema_field(CustomRigListProjectSerializer(allow_null=True))
    def get_project(self, obj: dict) -> dict | None:
        project_id = obj.get("project_id", None)
        return CustomRigListProjectSerializer({"id": project_id}).data if project_id else None

    @extend_schema_field(CustomRigListEMPSerializer(allow_null=True))
    def get_emp(self, obj: dict) -> dict | None:
        emp_id = obj.get("emp_id", None)
        return CustomRigListProjectSerializer({"id": emp_id}).data if emp_id else None


class RigListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


COMMON_DRILLSHIP_SERIALIZER_FIELDS = (
    "name",
    "manager",
    "design",
    "build_yard",
    "rig_status",
    "delivery_date",
    "special_survey_due",
    "end_of_last_contract",
    "months_in_operation_last_year",
    "months_in_operation_last_3_years",
    "design_score",
    "topside_design",
    "quarters_capacity",
    "hull_breadth",
    "hull_depth",
    "hull_length",
    "derrick_height",
    "derrick_capacity",
    "drawworks_power",
    "total_cranes",
    "crane_capacity",
    "total_bop_rams",
    "bop_diameter_wp_max",
    "bop_wp_max",
    "number_of_bop_stacks",
    "mudpump_quantity",
    "liquid_mud",
    "mud_total_power",
    "shaleshaker_total",
    "engine_power",
    "engine_quantity",
    "engine_total",
    "generator_power",
    "generator_quantity",
    "generator_total",
    "offline_stand_building",
    "auto_pipe_handling",
    "dual_activity",
    "drilltronic",
    "dynamic_drilling_guide",
    "process_automation_platform",
    "automatic_tripping",
    "closed_bus",
    "scr",
    "hybrid",
    "hvac_heat_recovery",
    "freshwater_cooling_systems",
    "seawater_cooling_systems",
    "operator_awareness_dashboard",
    "hpu_optimization",
    "optimized_heat_tracing_system",
    "floodlighting_optimization",
    "vfds_on_aux_machinery",
    "equipment_load",
    "drillfloor_efficiency",
    "rig_water_depth",
    "variable_load",
    "hull_concept_score",
    "hull_design_eco_score",
    "dp",
    "dp_class",
    "draft_depth",
    "displacement",
    "riser_on_board_outfitted",
    "riser_storage_inside_hull",
    "split_funnels_free_stern_deck",
    "dual_derrick",
    "active_heave_drawwork",
    "cmc_with_active_heave",
    "ram_system",
    "tripsaver",
    "day_rate",
    "spread_cost",
    "tugs_no_used",
)

COMMON_JACKUP_RIG_SERIALIZER_FIELDS = (
    "name",
    "manager",
    "design",
    "build_yard",
    "rig_status",
    "delivery_date",
    "special_survey_due",
    "end_of_last_contract",
    "months_in_operation_last_year",
    "months_in_operation_last_3_years",
    "design_score",
    "topside_design",
    "day_rate",
    "spread_cost",
    "tugs_no_used",
    "jack_up_time",
    "jack_down_time",
    "quarters_capacity",
    "rig_water_depth",
    "variable_load",
    "hull_breadth",
    "hull_depth",
    "hull_length",
    "derrick_height",
    "derrick_capacity",
    "drawworks_power",
    "total_cranes",
    "crane_capacity",
    "total_bop_rams",
    "bop_diameter_wp_max",
    "bop_wp_max",
    "number_of_bop_stacks",
    "mudpump_quantity",
    "liquid_mud",
    "mud_total_power",
    "shaleshaker_total",
    "engine_power",
    "engine_quantity",
    "engine_total",
    "generator_power",
    "generator_quantity",
    "generator_total",
    "offline_stand_building",
    "auto_pipe_handling",
    "dual_activity",
    "drilltronic",
    "dynamic_drilling_guide",
    "process_automation_platform",
    "automatic_tripping",
    "closed_bus",
    "scr",
    "hybrid",
    "hvac_heat_recovery",
    "freshwater_cooling_systems",
    "seawater_cooling_systems",
    "operator_awareness_dashboard",
    "hpu_optimization",
    "optimized_heat_tracing_system",
    "floodlighting_optimization",
    "vfds_on_aux_machinery",
    "cantilever_reach",
    "cantilever_lateral",
    "cantilever_capacity",
    "leg_length",
    "leg_spacing",
    "subsea_drilling",
    "enhanced_legs",
)

COMMON_SEMI_RIG_SERIALIZER_FIELDS = (
    "name",
    "manager",
    "design",
    "build_yard",
    "rig_status",
    "delivery_date",
    "special_survey_due",
    "end_of_last_contract",
    "months_in_operation_last_year",
    "months_in_operation_last_3_years",
    "design_score",
    "topside_design",
    "day_rate",
    "spread_cost",
    "tugs_no_used",
    "move_speed",
    "quarters_capacity",
    "rig_water_depth",
    "variable_load",
    "hull_breadth",
    "hull_depth",
    "hull_length",
    "derrick_height",
    "derrick_capacity",
    "drawworks_power",
    "total_cranes",
    "crane_capacity",
    "total_bop_rams",
    "bop_diameter_wp_max",
    "bop_wp_max",
    "number_of_bop_stacks",
    "mudpump_quantity",
    "liquid_mud",
    "mud_total_power",
    "shaleshaker_total",
    "engine_power",
    "engine_quantity",
    "engine_total",
    "generator_power",
    "generator_quantity",
    "generator_total",
    "offline_stand_building",
    "auto_pipe_handling",
    "dual_activity",
    "drilltronic",
    "dynamic_drilling_guide",
    "process_automation_platform",
    "automatic_tripping",
    "closed_bus",
    "scr",
    "hybrid",
    "hvac_heat_recovery",
    "freshwater_cooling_systems",
    "seawater_cooling_systems",
    "operator_awareness_dashboard",
    "hpu_optimization",
    "optimized_heat_tracing_system",
    "floodlighting_optimization",
    "vfds_on_aux_machinery",
    "equipment_load",
    "drillfloor_efficiency",
    "hull_concept_score",
    "hull_design_eco_score",
    "dp",
    "dp_class",
    "thruster_assist",
    "total_anchors",
    "anchor_standalone",
    "airgap",
    "draft_depth",
    "displacement",
    "dual_derrick",
    "active_heave_drawwork",
    "cmc_with_active_heave",
    "ram_system",
    "tripsaver",
)


class UpdateCustomJackupRigDraftSerializer(DraftSerializer, serializers.ModelSerializer):
    class Meta:
        model = CustomJackupRig
        fields: tuple[str, ...] = COMMON_JACKUP_RIG_SERIALIZER_FIELDS + ("draft",)


def UpdateCustomJackupRigSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class UpdateCustomJackupRigSerializer(UpdateCustomJackupRigDraftSerializer):
        class Meta(UpdateCustomJackupRigDraftSerializer.Meta):
            extra_kwargs = {
                'name': {'allow_blank': draft, 'required': not draft},
                'manager': {'allow_blank': draft, 'required': not draft},
                'design': {'allow_blank': draft, 'required': not draft},
                'build_yard': {'allow_blank': draft, 'required': not draft},
                'rig_status': {'allow_blank': draft, 'required': not draft},
                'delivery_date': {'allow_null': draft, 'required': not draft},
                'special_survey_due': {'allow_null': draft, 'required': not draft},
                'end_of_last_contract': {'allow_null': draft, 'required': not draft},
                'months_in_operation_last_year': {'allow_null': draft, 'required': not draft},
                'months_in_operation_last_3_years': {'allow_null': draft, 'required': not draft},
                'design_score': {'allow_blank': draft, 'required': not draft},
                'topside_design': {'allow_blank': draft, 'required': not draft},
                'jack_up_time': {'allow_null': draft, 'required': not draft},
                'jack_down_time': {'allow_null': draft, 'required': not draft},
                'quarters_capacity': {'allow_null': draft, 'required': not draft},
                'rig_water_depth': {'allow_null': draft, 'required': not draft},
                'variable_load': {'allow_null': draft, 'required': not draft},
                'hull_breadth': {'allow_null': draft, 'required': not draft},
                'hull_depth': {'allow_null': draft, 'required': not draft},
                'hull_length': {'allow_null': draft, 'required': not draft},
                'derrick_height': {'allow_null': draft, 'required': not draft},
                'derrick_capacity': {'allow_null': draft, 'required': not draft},
                'drawworks_power': {'allow_null': draft, 'required': not draft},
                'total_cranes': {'allow_null': draft, 'required': not draft},
                'crane_capacity': {'allow_null': draft, 'required': not draft},
                'total_bop_rams': {'allow_null': draft, 'required': not draft},
                'bop_diameter_wp_max': {'allow_null': draft, 'required': not draft},
                'bop_wp_max': {'allow_null': draft, 'required': not draft},
                'number_of_bop_stacks': {'allow_null': draft, 'required': not draft},
                'mudpump_quantity': {'allow_null': draft, 'required': not draft},
                'liquid_mud': {'allow_null': draft, 'required': not draft},
                'mud_total_power': {'allow_null': draft, 'required': not draft},
                'shaleshaker_total': {'allow_null': draft, 'required': not draft},
                'engine_power': {'allow_null': draft, 'required': not draft},
                'engine_quantity': {'allow_null': draft, 'required': not draft},
                'engine_total': {'allow_null': draft, 'required': not draft},
                'generator_power': {'allow_null': draft, 'required': not draft},
                'generator_quantity': {'allow_null': draft, 'required': not draft},
                'generator_total': {'allow_null': draft, 'required': not draft},
                'offline_stand_building': {'allow_null': draft, 'required': not draft},
                'auto_pipe_handling': {'allow_null': draft, 'required': not draft},
                'dual_activity': {'allow_null': draft, 'required': not draft},
                'drilltronic': {'allow_null': draft, 'required': not draft},
                'dynamic_drilling_guide': {'allow_null': draft, 'required': not draft},
                'process_automation_platform': {'allow_null': draft, 'required': not draft},
                'automatic_tripping': {'allow_null': draft, 'required': not draft},
                'closed_bus': {'allow_null': draft, 'required': not draft},
                'scr': {'allow_null': draft, 'required': not draft},
                'hybrid': {'allow_null': draft, 'required': not draft},
                'hvac_heat_recovery': {'allow_null': draft, 'required': not draft},
                'freshwater_cooling_systems': {'allow_null': draft, 'required': not draft},
                'seawater_cooling_systems': {'allow_null': draft, 'required': not draft},
                'operator_awareness_dashboard': {'allow_null': draft, 'required': not draft},
                'hpu_optimization': {'allow_null': draft, 'required': not draft},
                'optimized_heat_tracing_system': {'allow_null': draft, 'required': not draft},
                'floodlighting_optimization': {'allow_null': draft, 'required': not draft},
                'vfds_on_aux_machinery': {'allow_null': draft, 'required': not draft},
                'cantilever_reach': {'allow_null': draft, 'required': not draft},
                'cantilever_lateral': {'allow_null': draft, 'required': not draft},
                'cantilever_capacity': {'allow_null': draft, 'required': not draft},
                'leg_length': {'allow_null': draft, 'required': not draft},
                'leg_spacing': {'allow_null': draft, 'required': not draft},
                'subsea_drilling': {'allow_null': draft, 'required': not draft},
                'enhanced_legs': {'allow_null': draft, 'required': not draft},
                'tugs_no_used': {'allow_null': draft, 'required': not draft},
            }

    return UpdateCustomJackupRigSerializer


def CreateCustomJackupRigSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class CreateCustomJackupRigDraftSerializer(UpdateCustomJackupRigSerializerFactory(draft)):  # type: ignore
        project = serializers.IntegerField(required=False, allow_null=True)

        class Meta(UpdateCustomJackupRigSerializerFactory(draft).Meta):  # type: ignore
            fields = UpdateCustomJackupRigSerializerFactory(draft).Meta.fields + ("project",)  # type: ignore

    return CreateCustomJackupRigDraftSerializer


class CustomJackupRigDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomJackupRig
        fields = COMMON_JACKUP_RIG_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
            "draft",
        )


class CustomSemiRigDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomSemiRig
        fields = COMMON_SEMI_RIG_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
            "draft",
        )


class UpdateCustomSemiRigDraftSerializer(DraftSerializer, serializers.ModelSerializer):
    class Meta:
        model = CustomSemiRig
        fields: tuple[str, ...] = COMMON_SEMI_RIG_SERIALIZER_FIELDS + ("draft",)


def UpdateCustomSemiRigSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class UpdateCustomSemiRigSerializer(UpdateCustomSemiRigDraftSerializer):
        class Meta(UpdateCustomSemiRigDraftSerializer.Meta):
            extra_kwargs = {
                "name": dict(allow_blank=draft, required=not draft),
                "manager": dict(allow_blank=draft, required=not draft),
                "design": dict(allow_blank=draft, required=not draft),
                "build_yard": dict(allow_blank=draft, required=not draft),
                "rig_status": dict(allow_blank=draft, required=not draft),
                "delivery_date": dict(allow_null=draft, required=not draft),
                "special_survey_due": dict(allow_null=draft, required=not draft),
                "end_of_last_contract": dict(allow_null=draft, required=not draft),
                "months_in_operation_last_year": dict(allow_null=draft, required=not draft),
                "months_in_operation_last_3_years": dict(allow_null=draft, required=not draft),
                "design_score": dict(allow_blank=draft, required=not draft),
                "topside_design": dict(allow_blank=draft, required=not draft),
                "quarters_capacity": dict(allow_null=draft, required=not draft),
                "rig_water_depth": dict(allow_null=draft, required=not draft),
                "variable_load": dict(allow_null=draft, required=not draft),
                "hull_breadth": dict(allow_null=draft, required=not draft),
                "hull_depth": dict(allow_null=draft, required=not draft),
                "hull_length": dict(allow_null=draft, required=not draft),
                "derrick_height": dict(allow_null=draft, required=not draft),
                "derrick_capacity": dict(allow_null=draft, required=not draft),
                "drawworks_power": dict(allow_null=draft, required=not draft),
                "total_cranes": dict(allow_null=draft, required=not draft),
                "crane_capacity": dict(allow_null=draft, required=not draft),
                "total_bop_rams": dict(allow_null=draft, required=not draft),
                "bop_diameter_wp_max": dict(allow_null=draft, required=not draft),
                "bop_wp_max": dict(allow_null=draft, required=not draft),
                "number_of_bop_stacks": dict(allow_null=draft, required=not draft),
                "mudpump_quantity": dict(allow_null=draft, required=not draft),
                "liquid_mud": dict(allow_null=draft, required=not draft),
                "mud_total_power": dict(allow_null=draft, required=not draft),
                "shaleshaker_total": dict(allow_null=draft, required=not draft),
                "engine_power": dict(allow_null=draft, required=not draft),
                "engine_quantity": dict(allow_null=draft, required=not draft),
                "engine_total": dict(allow_null=draft, required=not draft),
                "generator_power": dict(allow_null=draft, required=not draft),
                "generator_quantity": dict(allow_null=draft, required=not draft),
                "generator_total": dict(allow_null=draft, required=not draft),
                "offline_stand_building": dict(allow_null=draft, required=not draft),
                "auto_pipe_handling": dict(allow_null=draft, required=not draft),
                "dual_activity": dict(allow_null=draft, required=not draft),
                "drilltronic": dict(allow_null=draft, required=not draft),
                "dynamic_drilling_guide": dict(allow_null=draft, required=not draft),
                "process_automation_platform": dict(allow_null=draft, required=not draft),
                "automatic_tripping": dict(allow_null=draft, required=not draft),
                "closed_bus": dict(allow_null=draft, required=not draft),
                "scr": dict(allow_null=draft, required=not draft),
                "hybrid": dict(allow_null=draft, required=not draft),
                "hvac_heat_recovery": dict(allow_null=draft, required=not draft),
                "freshwater_cooling_systems": dict(allow_null=draft, required=not draft),
                "seawater_cooling_systems": dict(allow_null=draft, required=not draft),
                "operator_awareness_dashboard": dict(allow_null=draft, required=not draft),
                "hpu_optimization": dict(allow_null=draft, required=not draft),
                "optimized_heat_tracing_system": dict(allow_null=draft, required=not draft),
                "floodlighting_optimization": dict(allow_null=draft, required=not draft),
                "vfds_on_aux_machinery": dict(allow_null=draft, required=not draft),
                "equipment_load": dict(allow_blank=draft, required=not draft),
                "drillfloor_efficiency": dict(allow_blank=draft, required=not draft),
                "hull_concept_score": dict(allow_null=draft, required=not draft),
                "hull_design_eco_score": dict(allow_null=draft, required=not draft),
                "dp": dict(allow_null=draft, required=not draft),
                "dp_class": dict(allow_blank=draft, required=not draft),
                "thruster_assist": dict(allow_null=draft, required=not draft),
                "total_anchors": dict(allow_null=draft, required=not draft),
                "anchor_standalone": dict(allow_null=draft, required=not draft),
                "airgap": dict(allow_blank=draft, required=not draft),
                "draft_depth": dict(allow_null=draft, required=not draft),
                "displacement": dict(allow_null=draft, required=not draft),
                "dual_derrick": dict(allow_null=draft, required=not draft),
                "active_heave_drawwork": dict(allow_null=draft, required=not draft),
                "cmc_with_active_heave": dict(allow_null=draft, required=not draft),
                "ram_system": dict(allow_null=draft, required=not draft),
                "tripsaver": dict(allow_null=draft, required=not draft),
                'tugs_no_used': {'allow_null': draft, 'required': not draft},
                "move_speed": {"allow_null": draft, "required": not draft},
            }

    return UpdateCustomSemiRigSerializer


def CreateCustomSemiRigSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class CreateCustomSemiRigSerializer(UpdateCustomSemiRigSerializerFactory(draft)):  # type: ignore
        project = serializers.IntegerField(required=False, allow_null=True)

        class Meta(UpdateCustomSemiRigSerializerFactory(draft).Meta):  # type: ignore
            fields = UpdateCustomSemiRigSerializerFactory(draft).Meta.fields + ("project",)  # type: ignore

    return CreateCustomSemiRigSerializer


class ConceptJackupRigDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptJackupRig
        fields = COMMON_JACKUP_RIG_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
        )


class ConceptSemiRigDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptSemiRig
        fields = COMMON_SEMI_RIG_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
        )


class UpdateCustomDrillshipDraftSerializer(DraftSerializer, serializers.ModelSerializer):
    class Meta:
        model = CustomDrillship
        fields: tuple[str, ...] = COMMON_DRILLSHIP_SERIALIZER_FIELDS + ("draft",)


def UpdateCustomDrillshipSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class UpdateCustomDrillshipSerializer(UpdateCustomDrillshipDraftSerializer):
        class Meta(UpdateCustomDrillshipDraftSerializer.Meta):
            pass
            extra_kwargs = {
                "name": dict(allow_blank=draft, required=not draft),
                "manager": dict(allow_blank=draft, required=not draft),
                "design": dict(allow_blank=draft, required=not draft),
                "build_yard": dict(allow_blank=draft, required=not draft),
                "rig_status": dict(allow_blank=draft, required=not draft),
                "delivery_date": dict(allow_null=draft, required=not draft),
                "special_survey_due": dict(allow_null=draft, required=not draft),
                "end_of_last_contract": dict(allow_null=draft, required=not draft),
                "months_in_operation_last_year": dict(allow_null=draft, required=not draft),
                "months_in_operation_last_3_years": dict(allow_null=draft, required=not draft),
                "design_score": dict(allow_blank=draft, required=not draft),
                "topside_design": dict(allow_blank=draft, required=not draft),
                "quarters_capacity": dict(allow_null=draft, required=not draft),
                "hull_breadth": dict(allow_null=draft, required=not draft),
                "hull_depth": dict(allow_null=draft, required=not draft),
                "hull_length": dict(allow_null=draft, required=not draft),
                "derrick_height": dict(allow_null=draft, required=not draft),
                "derrick_capacity": dict(allow_null=draft, required=not draft),
                "drawworks_power": dict(allow_null=draft, required=not draft),
                "total_cranes": dict(allow_null=draft, required=not draft),
                "crane_capacity": dict(allow_null=draft, required=not draft),
                "total_bop_rams": dict(allow_null=draft, required=not draft),
                "bop_diameter_wp_max": dict(allow_null=draft, required=not draft),
                "bop_wp_max": dict(allow_null=draft, required=not draft),
                "number_of_bop_stacks": dict(allow_null=draft, required=not draft),
                "mudpump_quantity": dict(allow_null=draft, required=not draft),
                "liquid_mud": dict(allow_null=draft, required=not draft),
                "mud_total_power": dict(allow_null=draft, required=not draft),
                "shaleshaker_total": dict(allow_null=draft, required=not draft),
                "engine_power": dict(allow_null=draft, required=not draft),
                "engine_quantity": dict(allow_null=draft, required=not draft),
                "engine_total": dict(allow_null=draft, required=not draft),
                "generator_power": dict(allow_null=draft, required=not draft),
                "generator_quantity": dict(allow_null=draft, required=not draft),
                "generator_total": dict(allow_null=draft, required=not draft),
                "offline_stand_building": dict(allow_null=draft, required=not draft),
                "auto_pipe_handling": dict(allow_null=draft, required=not draft),
                "dual_activity": dict(allow_null=draft, required=not draft),
                "drilltronic": dict(allow_null=draft, required=not draft),
                "dynamic_drilling_guide": dict(allow_null=draft, required=not draft),
                "process_automation_platform": dict(allow_null=draft, required=not draft),
                "automatic_tripping": dict(allow_null=draft, required=not draft),
                "closed_bus": dict(allow_null=draft, required=not draft),
                "scr": dict(allow_null=draft, required=not draft),
                "hybrid": dict(allow_null=draft, required=not draft),
                "hvac_heat_recovery": dict(allow_null=draft, required=not draft),
                "freshwater_cooling_systems": dict(allow_null=draft, required=not draft),
                "seawater_cooling_systems": dict(allow_null=draft, required=not draft),
                "operator_awareness_dashboard": dict(allow_null=draft, required=not draft),
                "hpu_optimization": dict(allow_null=draft, required=not draft),
                "optimized_heat_tracing_system": dict(allow_null=draft, required=not draft),
                "floodlighting_optimization": dict(allow_null=draft, required=not draft),
                "vfds_on_aux_machinery": dict(allow_null=draft, required=not draft),
                "equipment_load": dict(allow_blank=draft, required=not draft),
                "drillfloor_efficiency": dict(allow_blank=draft, required=not draft),
                "rig_water_depth": dict(allow_null=draft, required=not draft),
                "variable_load": dict(allow_null=draft, required=not draft),
                "hull_concept_score": dict(allow_null=draft, required=not draft),
                "hull_design_eco_score": dict(allow_null=draft, required=not draft),
                "dp": dict(allow_null=draft, required=not draft),
                "dp_class": dict(allow_blank=draft, required=not draft),
                "draft_depth": dict(allow_null=draft, required=not draft),
                "displacement": dict(allow_null=draft, required=not draft),
                "riser_on_board_outfitted": dict(allow_null=draft, required=not draft),
                "riser_storage_inside_hull": dict(allow_null=draft, required=not draft),
                "split_funnels_free_stern_deck": dict(allow_null=draft, required=not draft),
                "dual_derrick": dict(allow_null=draft, required=not draft),
                "active_heave_drawwork": dict(allow_null=draft, required=not draft),
                "cmc_with_active_heave": dict(allow_null=draft, required=not draft),
                "ram_system": dict(allow_null=draft, required=not draft),
                "tripsaver": dict(allow_null=draft, required=not draft),
                'tugs_no_used': {'allow_null': draft, 'required': not draft},
            }

    return UpdateCustomDrillshipSerializer


def CreateCustomDrillshipSerializerFactory(draft: bool) -> type[serializers.ModelSerializer]:
    class CreateCustomDrillshipSerializer(UpdateCustomDrillshipSerializerFactory(draft)):  # type: ignore
        project = serializers.IntegerField(required=False, allow_null=True)

        class Meta(UpdateCustomDrillshipSerializerFactory(draft).Meta):  # type: ignore
            fields = UpdateCustomDrillshipSerializerFactory(draft).Meta.fields + ("project",)  # type: ignore

    return CreateCustomDrillshipSerializer


class ConceptDrillshipDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptDrillship
        fields = COMMON_DRILLSHIP_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
        )


class CustomDrillshipDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDrillship
        fields = COMMON_DRILLSHIP_SERIALIZER_FIELDS + (
            "id",
            "created_at",
            "updated_at",
            "draft",
        )
