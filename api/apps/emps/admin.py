from django.contrib import admin

from apps.emps.models import EMP, ConceptEMPElement, CustomEMPElement


@admin.register(ConceptEMPElement)
class ConceptEMPElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subarea')
    search_fields = ('id', 'name', 'subarea')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class CustomEMPElementInline(admin.TabularInline):
    model = CustomEMPElement
    autocomplete_fields = ('concept_emp_element',)
    extra = 0


@admin.register(EMP)
class EMPAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "start_date",
        "end_date",
    )
    search_fields = (
        "id",
        "name",
    )
    list_filter = ("created_at", "updated_at", "start_date", "end_date")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CustomEMPElementInline]
