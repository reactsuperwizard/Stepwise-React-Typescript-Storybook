from django.contrib import admin

from apps.emissions.models import (
    BaselineCO2,
    BaselineNOX,
    CompleteHelicopterUse,
    CompleteVesselUse,
    PlannedHelicopterUse,
    PlannedVesselUse,
    TargetCO2,
    TargetCO2Reduction,
    TargetNOX,
    TargetNOXReduction,
    WellCompleteStepMaterial,
    WellName,
    WellPlannedStepMaterial,
)


@admin.register(WellName)
class WellNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'tenant')
    autocomplete_fields = ('tenant',)
    search_fields = ('id', 'name')


@admin.register(PlannedVesselUse)
class PlannedVesselUseAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'vessel_type', 'duration', 'season')
    search_fields = ('id',)
    autocomplete_fields = ('well_planner', 'vessel_type')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('season',)


@admin.register(CompleteVesselUse)
class CompleteVesselUseAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'vessel_type', 'duration', 'season', 'approved')
    search_fields = ('id',)
    autocomplete_fields = ('well_planner', 'vessel_type')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('approved', 'season')


@admin.register(WellPlannedStepMaterial)
class WellPlannedStepMaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'step', 'material_type', 'quantity', 'quota')
    autocomplete_fields = ('step', 'material_type')
    search_fields = ('id', 'step__well_planner__name__name', 'material_type__type')


@admin.register(WellCompleteStepMaterial)
class WellCompleteStepMaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'step', 'material_type', 'quantity', 'quota')
    autocomplete_fields = ('step', 'material_type')
    search_fields = ('id', 'step__well_planner__name__name', 'material_type__type')


@admin.register(PlannedHelicopterUse)
class PlannedHelicopterUseAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'helicopter_type', 'trips', 'trip_duration')
    search_fields = ('id',)
    autocomplete_fields = ('well_planner', 'helicopter_type')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CompleteHelicopterUse)
class CompleteHelicopterUseAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'helicopter_type', 'trips', 'trip_duration', 'approved')
    search_fields = ('id',)
    autocomplete_fields = ('well_planner', 'helicopter_type')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BaselineCO2)
class BaselineCO2Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'planned_step',
        'asset',
        'vessels',
        'helicopters',
        'materials',
        'external_energy_supply',
        'datetime',
    )
    search_fields = ('id',)
    autocomplete_fields = ('planned_step',)


class TargetCO2ReductionInline(admin.TabularInline):
    model = TargetCO2Reduction
    autocomplete_fields = ('emission_reduction_initiative',)
    extra = 0


@admin.register(TargetCO2)
class TargetCO2Admin(admin.ModelAdmin):
    list_display = (
        'id',
        'planned_step',
        'asset',
        'vessels',
        'helicopters',
        'materials',
        'external_energy_supply',
        'datetime',
    )
    search_fields = ('id',)
    autocomplete_fields = ('planned_step',)
    inlines = [TargetCO2ReductionInline]


@admin.register(TargetCO2Reduction)
class TargetCO2ReductionAdmin(admin.ModelAdmin):
    list_display = ('id', 'target', 'emission_reduction_initiative', 'value')
    search_fields = ('id',)
    autocomplete_fields = ('target', 'emission_reduction_initiative')


@admin.register(BaselineNOX)
class BaselineNOXAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'planned_step',
        'asset',
        'vessels',
        'helicopters',
        'external_energy_supply',
        'datetime',
    )
    search_fields = ('id',)
    autocomplete_fields = ('planned_step',)


class TargetNOXReductionInline(admin.TabularInline):
    model = TargetNOXReduction
    autocomplete_fields = ('emission_reduction_initiative',)
    extra = 0


@admin.register(TargetNOX)
class TargetNOXAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'planned_step',
        'asset',
        'vessels',
        'helicopters',
        'external_energy_supply',
        'datetime',
    )
    search_fields = ('id',)
    autocomplete_fields = ('planned_step',)
    inlines = [TargetNOXReductionInline]


@admin.register(TargetNOXReduction)
class TargetNOXReductionAdmin(admin.ModelAdmin):
    list_display = ('id', 'target', 'emission_reduction_initiative', 'value')
    search_fields = ('id',)
    autocomplete_fields = ('target', 'emission_reduction_initiative')
