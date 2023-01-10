from django.contrib import admin
from django.db import transaction
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedStackedInline

from apps.emissions.models import CompleteHelicopterUse, CompleteVesselUse, PlannedHelicopterUse, PlannedVesselUse
from apps.rigs.tasks import sync_all_custom_well_co2_calculations_task
from apps.wells.forms import WellPlannerCompleteStepForm, WellPlannerPlannedStepForm
from apps.wells.models import (
    ConceptWell,
    CustomWell,
    WellPlanner,
    WellPlannerCompleteStep,
    WellPlannerPlannedStep,
    WellReferenceMaterial,
)


@admin.register(ConceptWell)
class ConceptWellAdmin(admin.ModelAdmin):
    search_fields = ('id', 'name', 'type')
    list_display = ('id', 'name', 'type', 'water_depth')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')


@admin.register(CustomWell)
class CustomWellAdmin(admin.ModelAdmin):
    search_fields = ('id', 'name', 'type')
    list_display = ('id', 'name', 'type', 'water_depth', 'tenant')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('tenant', 'creator', 'project')
    list_filter = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        updated = obj.pk is not None
        super().save_model(request, obj, form, change)

        if updated:
            transaction.on_commit(lambda: sync_all_custom_well_co2_calculations_task.delay(obj.pk))


class PlannedHelicopterUseInline(admin.TabularInline):
    model = PlannedHelicopterUse
    extra = 0
    autocomplete_fields = ('helicopter_type',)


class CompleteHelicopterUseInline(admin.TabularInline):
    model = CompleteHelicopterUse

    extra = 0
    autocomplete_fields = ('helicopter_type',)


class PlannedVesselUseInline(admin.TabularInline):
    model = PlannedVesselUse
    extra = 0
    autocomplete_fields = ('vessel_type',)


class CompleteVesselUseInline(admin.TabularInline):
    model = CompleteVesselUse
    extra = 0
    autocomplete_fields = ('vessel_type',)


class WellPlannerPlannedStepInline(OrderedStackedInline):
    model = WellPlannerPlannedStep
    extra = 0
    autocomplete_fields = ("emission_reduction_initiatives",)
    readonly_fields = ('move_up_down_links',)


class WellPlannerCompleteStepInline(OrderedStackedInline):
    model = WellPlannerCompleteStep
    extra = 0
    autocomplete_fields = ("emission_reduction_initiatives",)
    readonly_fields = ('move_up_down_links',)


@admin.register(WellPlannerPlannedStep)
class WellPlannerPlannedStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'phase', 'season', 'mode', 'duration', 'improved_duration', 'order')
    autocomplete_fields = (
        'well_planner',
        "emission_reduction_initiatives",
    )
    search_fields = ('id', 'well_planner__name__name', 'phase__name')
    readonly_fields = ('created_at', 'updated_at')
    form = WellPlannerPlannedStepForm


@admin.register(WellPlannerCompleteStep)
class WellPlannerCompleteStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'well_planner', 'phase', 'season', 'mode', 'duration', 'order', 'approved')
    autocomplete_fields = (
        'well_planner',
        "emission_reduction_initiatives",
    )
    search_fields = ('id', 'well_planner__name__name', 'phase__name')
    readonly_fields = ('created_at', 'updated_at')
    form = WellPlannerCompleteStepForm


@admin.register(WellPlanner)
class WellPlannerAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'sidetrack',
        'asset',
        'type',
        'location',
        'field',
        'current_step',
        'planned_start_date',
        'actual_start_date',
        'asset',
        'deleted',
    )
    search_fields = ('id', 'name__name', 'sidetrack', 'description')
    autocomplete_fields = ("asset", "baseline", "emission_management_plan", "name")
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('planned_start_date', 'actual_start_date', 'deleted', 'type', 'current_step')

    inlines = [
        PlannedHelicopterUseInline,
        CompleteHelicopterUseInline,
        PlannedVesselUseInline,
        CompleteVesselUseInline,
        WellPlannerPlannedStepInline,
        WellPlannerCompleteStepInline,
    ]


@admin.register(WellReferenceMaterial)
class WellReferenceMaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'details', 'vehicles', 'planning', 'complete')
    search_fields = ('id',)
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at', 'updated_at')
