from django.contrib import admin
from django.db import transaction

from apps.projects.models import Plan, PlanWellRelation, Project
from apps.rigs.tasks import sync_all_plan_co2_calculations_task, sync_all_project_co2_calculations_task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'creator', 'created_at')
    search_fields = ('id', 'name', 'description')
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = (
        'tenant',
        'creator',
    )

    def save_model(self, request, obj, form, change):
        updated = obj.pk is not None
        super().save_model(request, obj, form, change)

        if updated:
            transaction.on_commit(lambda: sync_all_project_co2_calculations_task.delay(obj.pk))


class PlanWellInline(admin.StackedInline):
    model = PlanWellRelation
    autocomplete_fields = ('well',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        transaction.on_commit(lambda: sync_all_plan_co2_calculations_task.delay(obj.plan_id))


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project', 'created_at')
    search_fields = ('id', 'name', 'description')
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = (
        'project',
        'reference_operation_jackup',
        'reference_operation_semi',
        'reference_operation_drillship',
    )

    inlines = [PlanWellInline]

    def save_model(self, request, obj, form, change):
        updated = obj.pk is not None
        super().save_model(request, obj, form, change)

        if updated:
            transaction.on_commit(lambda: sync_all_plan_co2_calculations_task.delay(obj.pk))


@admin.register(PlanWellRelation)
class PlanWellRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'well', 'order')
    search_fields = ('id',)
    autocomplete_fields = ('plan', 'well')
    readonly_fields = ('order',)
