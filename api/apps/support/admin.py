from django.contrib import admin
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedModelAdmin, OrderedStackedInline

from apps.support.models import Faq, FaqElement


@admin.register(FaqElement)
class FaqElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'faq', 'created_at', 'updated_at')
    search_fields = ('question',)
    autocomplete_fields = ('faq',)


class FaqElementInline(OrderedStackedInline):
    model = FaqElement
    fields = (
        'question',
        'answer',
        'draft',
        'move_up_down_links',
    )
    readonly_fields = ('move_up_down_links',)
    ordering = ('order',)
    extra = 0


@admin.register(Faq)
class FaqAdmin(OrderedInlineModelAdminMixin, OrderedModelAdmin):
    list_display = ('title', 'draft', 'created_at', 'updated_at', 'move_up_down_links')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('title',)

    inlines = [FaqElementInline]
