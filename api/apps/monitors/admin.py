from django.contrib import admin
from django.db import transaction
from django.shortcuts import render

from apps.monitors.forms import TEST_MONITOR_FUNCTION_ACTION, MonitorFunctionForm, MonitorFunctionTestForm
from apps.monitors.models import Monitor, MonitorElement, MonitorElementPhase, MonitorFunction, MonitorFunctionValue
from apps.monitors.tasks import sync_all_monitor_function_values_task


class MonitorElementInline(admin.StackedInline):
    model = MonitorElement
    extra = 0
    max_num = 0
    fields = (
        'name',
        'description',
        'value_unit',
        'value_title',
        'draft',
    )
    readonly_fields = fields


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'name', 'description', 'start_date', 'end_date', 'draft')
    search_fields = ('id', 'name', 'description')
    list_filter = ('start_date', 'end_date', 'created_at', 'updated_at')
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [
        MonitorElementInline,
    ]


class MonitorElementPhaseInline(admin.StackedInline):
    model = MonitorElementPhase
    fields = ('name', 'start_date', 'end_date', 'target', 'baseline')


@admin.register(MonitorElement)
class MonitorElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'monitor', 'name', 'monitor_function', 'value_unit', 'value_title', 'draft')
    search_fields = ('id', 'name', 'description')
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = ('monitor', 'monitor_function')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MonitorElementPhaseInline]


@admin.register(MonitorElementPhase)
class MonitorElementPhaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'monitor_element', 'name', 'start_date', 'end_date', 'target', 'baseline')
    autocomplete_fields = ('monitor_element',)
    search_fields = ('id', 'name')
    list_filter = ('created_at', 'updated_at')


@admin.register(MonitorFunction)
class MonitorFunctionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'vessel', 'type', 'start_date', 'draft')
    search_fields = ('id', 'name')
    list_filter = ('created_at', 'updated_at', 'type')
    autocomplete_fields = ('vessel',)
    readonly_fields = ('created_at', 'updated_at')
    form = MonitorFunctionForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.draft:
            return

        if any(
            [
                obj.vessel != form.initial.get('vessel'),
                obj.start_date != form.initial.get('start_date'),
                obj.monitor_function_source != form.initial.get('monitor_function_source'),
                obj.draft != form.initial.get('draft'),
            ]
        ):
            transaction.on_commit(lambda: sync_all_monitor_function_values_task.delay(obj.pk))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.method == 'POST' and TEST_MONITOR_FUNCTION_ACTION in request.POST:
            obj = self.get_object(request, object_id)
            form = MonitorFunctionTestForm(request.POST, request.FILES, instance=obj)
            form.is_valid()

            context = {
                'title': 'Test Function Result',
                'form': form,
            }
            return render(request, 'admin/monitors/monitor_function_test_results.html', context=context)

        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        if request.method == 'POST' and TEST_MONITOR_FUNCTION_ACTION in request.POST:
            form = MonitorFunctionTestForm(request.POST, request.FILES)
            form.is_valid()

            context = {
                'title': 'Test Function Result',
                'form': form,
            }
            return render(request, 'admin/monitors/monitor_function_test_results.html', context=context)

        return super().add_view(request, form_url=form_url, extra_context=extra_context)


@admin.register(MonitorFunctionValue)
class MonitorFunctionValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'monitor_function', 'value', 'date')
    autocomplete_fields = ('monitor_function',)
    search_fields = (
        'id',
        'monitor_function__name',
    )
    list_filter = ('date',)
