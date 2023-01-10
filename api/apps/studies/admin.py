from django.contrib import admin
from django.db import models

from apps.studies.models import (
    StudyElement,
    StudyElementDrillshipRelation,
    StudyElementJackupRigRelation,
    StudyElementSemiRigRelation,
    StudyMetric,
)


def StudyElementRigRelationInlineFactory(Model: type[models.Model]) -> type[admin.TabularInline]:
    class StudyElementRigRelationInline(admin.TabularInline):
        model = Model
        autocomplete_fields = ('rig',)

    return StudyElementRigRelationInline


@admin.register(StudyElement)
class StudyElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'title', 'metric', 'plan', 'creator', 'order', 'created_at')
    search_fields = (
        'id',
        'title',
    )
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = ('project', 'metric', 'plan', 'creator')
    inlines = [
        StudyElementRigRelationInlineFactory(StudyElementSemiRigRelation),
        StudyElementRigRelationInlineFactory(StudyElementJackupRigRelation),
        StudyElementRigRelationInlineFactory(StudyElementDrillshipRelation),
    ]


@admin.register(StudyElementSemiRigRelation)
@admin.register(StudyElementJackupRigRelation)
@admin.register(StudyElementDrillshipRelation)
class StudyElementRigRelationAdmin(admin.ModelAdmin):
    search_fields = ('id',)
    list_display = ('id', 'study_element', 'rig', 'value')
    autocomplete_fields = ('study_element', 'rig')


@admin.register(StudyMetric)
class StudyMetricAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'unit',
        "is_jackup_compatible",
        "is_semi_compatible",
        "is_drillship_compatible",
    )
    search_fields = ('id', 'name', 'unit')
