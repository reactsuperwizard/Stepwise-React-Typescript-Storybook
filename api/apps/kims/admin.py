from django.contrib import admin
from django.db import transaction

from apps.emissions.models import Asset
from apps.kims.models import KimsAPI, Tag, TagValue, Vessel
from apps.kims.services import get_tags_sync_period
from apps.kims.tasks import sync_vessel_tags_task, sync_vessel_tags_values_task


@admin.register(KimsAPI)
class KimsAPIAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_url',
    )
    search_fields = ('id', 'base_url')
    readonly_fields = ('created_at', 'updated_at')


class TagInline(admin.StackedInline):
    model = Tag
    readonly_fields = (
        'name',
        'data_type',
    )
    can_delete = False
    extra = 0
    max_num = 0


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'kims_vessel_id',
        'kims_api',
        'tags_synced_at',
        'is_active',
    )
    inlines = (TagInline,)
    readonly_fields = ('tags_synced_at',)
    search_fields = ('id', 'kims_vessel_id', 'name')
    autocomplete_fields = ('kims_api',)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if obj.is_active and obj.tags_synced_at is None:
            start, end = get_tags_sync_period(obj)
            transaction.on_commit(
                lambda: sync_vessel_tags_task.apply_async(
                    args=(
                        obj.kims_api_id,
                        obj.pk,
                    ),
                    link=sync_vessel_tags_values_task.si(
                        obj.pk,
                        start.isoformat(),
                        end.isoformat(),
                    ),
                )
            )

        super().save_model(request, obj, form, change)

        Asset.objects.live().filter(vessel=obj).exclude(name=obj.name).update(vessel=None)
        Asset.objects.live().filter(name=obj.name).update(vessel=obj)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'vessel', 'name', 'data_type', 'deleted')
    search_fields = (
        'vessel__kims_vessel_id',
        'name',
    )
    list_filter = ('deleted',)
    autocomplete_fields = ('vessel',)

    def get_queryset(self, request):
        return Tag.objects.all().select_related('vessel')


@admin.register(TagValue)
class TagValueAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'kims_vessel_id',
        'tag',
        'mean',
        'average',
        'date',
    )
    search_fields = (
        'tag__vessel__name',
        'tag__name',
    )
    list_filter = ('date',)
    ordering = ('-date',)
    autocomplete_fields = ('tag',)

    def get_queryset(self, request):
        return TagValue.objects.all().select_related('tag', 'tag__vessel')

    @admin.display(ordering='tag__vessel__name', description='K-IMS Vessel ID')
    def kims_vessel_id(self, obj: TagValue) -> str:
        return obj.tag.vessel.kims_vessel_id
