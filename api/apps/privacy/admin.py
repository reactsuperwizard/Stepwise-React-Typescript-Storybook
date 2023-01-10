import logging
from typing import cast

from django.contrib import admin, messages
from django.core.handlers.wsgi import WSGIRequest
from django.db import models

from apps.privacy.models import DeleteAccountRequest, PrivacyPolicy, PrivacyPolicyConsent
from apps.privacy.services import activate_policy

logger = logging.getLogger(__name__)


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_active',
        'created_at',
    )
    readonly_fields = ('is_active',)
    actions = ['activate_policy']

    @admin.action(description='Activate privacy policy')
    def activate_policy(self, request: WSGIRequest, queryset: models.QuerySet['PrivacyPolicy']) -> None:
        logger.info('Activating new privacy policy')

        if queryset.count() > 1:
            self.message_user(
                request, "Only one privacy policy can be activated. Please select only one policy.", messages.ERROR
            )
        else:
            new_policy = cast(PrivacyPolicy, queryset.first())

            try:
                activate_policy(new_policy)
                self.message_user(request, "Privacy policy has been activated.", messages.SUCCESS)
                logger.info(f'Activated PrivacyPolicy(pk={new_policy.pk})')
            except ValueError as e:
                self.message_user(request, str(e), messages.ERROR)
                logger.info(f'Unable to activate PrivacyPolicy(pk={new_policy.pk}). Error: {str(e)}')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_active = False

        super().save_model(request, obj, form, change)


@admin.register(PrivacyPolicyConsent)
class PrivacyPolicyConsentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'policy',
        'revoked_at',
    )
    raw_id_fields = (
        'user',
        'policy',
    )


@admin.register(DeleteAccountRequest)
class DeleteAccountRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'execute_at', 'is_active')
    readonly_fields = ('is_active',)
    autocomplete_fields = ('user',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_active = True

        super().save_model(request, obj, form, change)
