from django.contrib import admin
from django.db import transaction

from apps.rigs.models import (
    ConceptDrillship,
    ConceptJackupRig,
    ConceptSemiRig,
    CustomDrillship,
    CustomJackupPlanCO2,
    CustomJackupRig,
    CustomJackupSubareaScore,
    CustomSemiPlanCO2,
    CustomSemiRig,
    CustomSemiSubareaScore,
)
from apps.rigs.tasks import sync_custom_jackup_subarea_score_task, sync_custom_semi_subarea_score_task


@admin.register(ConceptSemiRig)
@admin.register(ConceptJackupRig)
@admin.register(ConceptDrillship)
class ConceptRigAdmin(admin.ModelAdmin):
    search_fields = (
        "id",
        "name",
    )
    list_display = ("id", "name", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("created_at", "updated_at")


@admin.register(CustomDrillship)
class CustomRigAdmin(admin.ModelAdmin):
    search_fields = (
        "id",
        "name",
    )
    list_display = ("id", "name", "tenant", "creator", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("tenant", "creator", "emp", "project")
    list_filter = ("created_at", "updated_at")


@admin.register(CustomJackupRig)
class CustomJackupRigAdmin(CustomRigAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.draft:
            transaction.on_commit(lambda: sync_custom_jackup_subarea_score_task(obj.pk))


@admin.register(CustomSemiRig)
class CustomSemiRigAdmin(CustomRigAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not obj.draft:
            transaction.on_commit(lambda: sync_custom_semi_subarea_score_task(obj.pk))


@admin.register(CustomJackupSubareaScore)
@admin.register(CustomSemiSubareaScore)
class CustomSubareaScoreAdmin(admin.ModelAdmin):
    list_display = ("id", "rig", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("rig",)
    search_fields = ("id",)


@admin.register(CustomJackupPlanCO2)
@admin.register(CustomSemiPlanCO2)
class CustomRigPlanCO2Admin(admin.ModelAdmin):
    list_display = ("id", "rig", "plan", "created_at", "updated_at")
    autocomplete_fields = (
        "rig",
        "plan",
    )
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    search_fields = ('id',)
