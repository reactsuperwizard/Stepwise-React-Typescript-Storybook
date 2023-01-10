import logging
from typing import Any

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db import models, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect

from apps.tenants import services as tenants_services
from apps.tenants.forms import UserAdminCreationForm, UserAdminForm
from apps.tenants.models import Tenant, TenantInvitation, TenantUserRelation, User
from apps.tenants.services import invite_tenant_user

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminForm
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            'Profile',
            {
                'fields': ('profile_image', 'company_name', 'phone_number', 'company', 'role'),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'company', 'role', 'password1', 'password2'),
            },
        ),
    )

    def save_model(self, request, user, form, change):
        if not change:
            user.email = user.username
            user.first_name = user.first_name or ''
            user.last_name = user.last_name or ''
            user.phone_number = user.phone_number or ''

        return super().save_model(request, user, form, change)


class TenantUserRelationInline(admin.TabularInline):
    model = TenantUserRelation
    raw_id_fields = ('tenant', 'user')


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "subdomain", "is_active")
    search_fields = ("id", "name", "subdomain")
    list_filter = ("is_active",)
    inlines = [
        TenantUserRelationInline,
    ]
    actions = ['send_tenant_is_ready_email']

    @admin.action(description='Send tenant is ready email')
    def send_tenant_is_ready_email(self, request: WSGIRequest, queryset: models.QuerySet['Tenant']) -> None:
        logger.info('Sending "tenant is ready" email')
        for tenant in queryset:
            try:
                tenants_services.send_tenant_is_ready_email(tenant)
                self.message_user(request, f"Sent the email for tenant \"{tenant.name}\"", messages.SUCCESS)
                logger.info('Sent email for Tenant(id=%s)', tenant.pk)
            except ValueError as e:
                self.message_user(request, str(e), messages.ERROR)
                logger.info('Unable to send email for Tenant(id=%s). Error: %s', tenant.pk, e)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        from apps.emissions.services import create_initial_concept_modes, create_initial_concept_phases

        created = obj.pk is None
        super().save_model(request, obj, form, change)

        if created:
            create_initial_concept_phases(obj)
            create_initial_concept_modes(obj)


@admin.register(TenantUserRelation)
class TenantUserRelationAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "user", "role")
    search_fields = ("id",)
    raw_id_fields = ("tenant", "user")


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "tenant", "is_active")
    search_fields = (
        "email",
        "tenant__name",
    )
    readonly_fields = ("expires_at", "is_active", "status")
    exclude = ("token",)

    def add_view(self, request: HttpRequest, form_url: str = '', extra_context: Any = None) -> HttpResponse:
        try:
            return super().add_view(request, form_url=form_url, extra_context=extra_context)
        except ValidationError as e:
            self.message_user(request, '%s' % e, level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def save_model(self, request: HttpRequest, obj: TenantInvitation, form: Any, change: Any) -> None:
        if obj.pk is None:
            tenant_invitation = invite_tenant_user(**form.cleaned_data)
            obj.pk = tenant_invitation.pk
            return

        return super().save_model(request, obj, form, change)
