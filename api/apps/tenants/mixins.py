from django import forms
from django.utils.functional import cached_property
from django.views import View
from rest_framework.generics import get_object_or_404

from apps.tenants.models import Tenant, TenantUserRelation, UserRole


class TenantUserMixin(View):
    @cached_property
    def tenant_user(self) -> TenantUserRelation:
        return get_object_or_404(TenantUserRelation, tenant_id=self.kwargs['tenant_id'], user=self.request.user)


class TenantMixin(View):
    @cached_property
    def tenant(self) -> Tenant:
        return get_object_or_404(Tenant, pk=self.kwargs['tenant_id'])


class UserFormValidationMixin(forms.Form):
    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get('role')
        company = cleaned_data.get('company', None)
        if role != UserRole.ADMIN and not company:
            raise forms.ValidationError('Company is required for non-admin users!')

        return cleaned_data
