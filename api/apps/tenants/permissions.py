from django.http import HttpRequest
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from apps.tenants.models import TenantUserRelation, User, UserRole


class IsTenantUser(BasePermission):
    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return False

        return self.has_access_to_tenant(request.user, view)

    def has_access_to_tenant(self, user: User, view: APIView) -> bool:
        tenant_id = view.kwargs.get('tenant_id')

        if tenant_id is None:
            return False

        return TenantUserRelation.objects.filter(
            user=user,
            tenant_id=tenant_id,
        ).exists()


class IsAdminUser(BasePermission):
    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return False

        return request.user.role == UserRole.ADMIN
