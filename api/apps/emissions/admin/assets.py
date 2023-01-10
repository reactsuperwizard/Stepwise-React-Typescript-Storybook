from django.contrib import admin

from apps.emissions.forms import (
    AssetAdminForm,
    BaselineAdminForm,
    EmissionManagementPlanAdminForm,
    EmissionReductionInitiativeAdminForm,
)
from apps.emissions.models import (
    Asset,
    AssetReferenceMaterial,
    Baseline,
    BaselineInput,
    ConceptMode,
    ConceptPhase,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    EmissionReductionInitiativeInput,
    ExternalEnergySupply,
    HelicopterType,
    VesselType,
)
from apps.emissions.models.assets import MaterialType


class ExternalEnergySupplyInline(admin.TabularInline):
    model = ExternalEnergySupply
    extra = 0


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tenant', 'vessel', 'draft', 'deleted')
    autocomplete_fields = ('vessel',)
    search_fields = ('id', 'name')
    readonly_fields = ("created_at", "updated_at")
    list_filter = ('draft', 'deleted')
    form = AssetAdminForm

    inlines = [
        ExternalEnergySupplyInline,
    ]


@admin.register(AssetReferenceMaterial)
class AssetReferenceMaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'details', 'baseline', 'emp')
    search_fields = ('id',)
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BaselineInput)
class BaselineInputAdmin(admin.ModelAdmin):
    list_display = ('id', 'baseline', 'season', 'phase', 'mode', 'value')
    search_fields = ('id', 'baseline__name')
    autocomplete_fields = ('baseline', 'phase', 'mode')


class BaselineInputInline(admin.TabularInline):
    model = BaselineInput
    fields = ('season', 'phase', 'mode', 'value')
    can_delete = False


@admin.register(Baseline)
class BaselineAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'name', 'description', 'active', 'draft', 'deleted')
    search_fields = ('id', 'name', 'description')
    autocomplete_fields = ('asset',)
    list_filter = ('active', 'draft', 'deleted')
    inlines = [BaselineInputInline]
    form = BaselineAdminForm


class EmissionReductionInitiativeInputInline(admin.TabularInline):
    model = EmissionReductionInitiativeInput
    can_delete = False


@admin.register(EmissionManagementPlan)
class EmissionManagementPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'baseline', 'name', 'description', 'version', 'draft', 'active')
    search_fields = ('id', 'name')
    autocomplete_fields = ('baseline',)
    list_filter = ('draft', 'active')
    form = EmissionManagementPlanAdminForm


@admin.register(ConceptPhase)
class ConceptPhaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'name', 'transit')
    search_fields = ('id', 'name')
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CustomPhase)
class CustomPhaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'name', 'phase')
    search_fields = ('id', 'name')
    autocomplete_fields = ('asset', 'phase')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ConceptMode)
class ConceptModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'name', 'asset_types', 'transit')
    search_fields = ('id', 'name')
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CustomMode)
class CustomModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'name', 'mode')
    search_fields = ('id', 'name')
    autocomplete_fields = ('asset', 'mode')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmissionReductionInitiative)
class EmissionReductionInitiativeAdmin(admin.ModelAdmin):
    list_display = ('id', 'emission_management_plan', 'name', 'description', 'type', 'vendor', 'deployment_date')
    search_fields = ('id', 'name')
    autocomplete_fields = ('emission_management_plan',)
    list_filter = ('type',)
    inlines = [EmissionReductionInitiativeInputInline]
    form = EmissionReductionInitiativeAdminForm


@admin.register(EmissionReductionInitiativeInput)
class EmissionReductionInitiativeInputAdmin(admin.ModelAdmin):
    list_display = ('id', 'emission_reduction_initiative', 'phase', 'mode', 'value')
    search_fields = ('id', 'emission_reduction_initiative__name')
    autocomplete_fields = ('emission_reduction_initiative', 'phase', 'mode')


@admin.register(VesselType)
class VesselTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "type", "fuel_type", "deleted")
    search_fields = ("id", "type")
    autocomplete_fields = ("tenant",)
    list_filter = ("deleted",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(HelicopterType)
class HelicopterTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "type", "deleted")
    search_fields = ("id", "type")
    autocomplete_fields = ("tenant",)
    list_filter = ("deleted",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ExternalEnergySupply)
class ExternalEnergySupplyAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "asset", "capacity", "co2", "nox", "generator_efficiency_factor")
    search_fields = ("id", "type")
    autocomplete_fields = ("asset",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(MaterialType)
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "category", "type", "unit", "co2", "deleted")
    search_fields = ("id", "type")
    autocomplete_fields = ("tenant",)
    readonly_fields = ("created_at", "updated_at")
