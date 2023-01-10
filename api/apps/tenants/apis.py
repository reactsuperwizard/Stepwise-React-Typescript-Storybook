from axes.handlers.proxy import AxesProxyHandler
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.mixins import TenantMixin, TenantUserMixin
from apps.tenants.models import Tenant, TenantInvitation, User
from apps.tenants.permissions import IsTenantUser
from apps.tenants.serializers import (
    LockedSerializer,
    LoginSerializerFactory,
    MeAvatarUpdateSerializer,
    MeSerializer,
    MeUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetChangePasswordSerializer,
    PasswordResetSerializer,
    TenantInvitationSerializer,
    TenantInvitationSignupSerializer,
    TenantSerializer,
)
from apps.tenants.services import (
    accept_tenant_invitation,
    change_password_reset_password,
    change_user_password,
    decode_password_reset_token,
    login_tenant_user,
    reset_password,
    signup_user,
    update_user_avatar,
    update_user_profile,
)


class LoginApi(APIView):
    @extend_schema(request=LoginSerializerFactory(False), responses={200: MeSerializer}, summary="Log in")
    def post(self, request: Request, tenant_id: int) -> Response:
        locked = AxesProxyHandler().is_locked(request=request, credentials=request.data)
        serializer = LoginSerializerFactory(locked)(data=request.data, context=dict(request=request))
        serializer.is_valid(raise_exception=True)

        tenant_user = login_tenant_user(request=request, tenant_id=tenant_id, **serializer.validated_data)

        response_data = MeSerializer(tenant_user.user).data
        return Response(response_data, 200)


class LogoutApi(APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Log out")
    def post(self, request: Request, tenant_id: int) -> Response:
        logout(request)
        return Response(status=204)


class LockedApi(APIView):
    @extend_schema(responses={200: LockedSerializer}, summary="Get lockout status")
    def get(self, request: Request, tenant_id: int) -> Response:
        data = dict(locked=AxesProxyHandler().is_locked(request=request))

        return Response(data, 200)


class MeApi(TenantUserMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: MeSerializer}, summary="Get current user details")
    def get(self, request: Request, tenant_id: int) -> Response:
        response_data = MeSerializer(request.user).data
        return Response(response_data, status=200)


class MeUpdateApi(TenantUserMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(request=MeUpdateSerializer, responses={200: MeSerializer}, summary="Update current user details")
    def post(self, request: Request, tenant_id: int) -> Response:
        serializer = MeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_user_profile(user=self.tenant_user.user, **serializer.validated_data)

        self.tenant_user.user.refresh_from_db()
        response_data = MeSerializer(self.tenant_user.user).data
        return Response(response_data, status=200)


@method_decorator(ensure_csrf_cookie, 'get')
class TenantDetailsApi(APIView):
    @extend_schema(responses={200: TenantSerializer}, summary="Check tenant details")
    def get(self, request: Request, subdomain: str) -> Response:
        tenant = get_object_or_404(Tenant, subdomain=subdomain)
        response_data = TenantSerializer(tenant).data
        return Response(response_data, status=200)


class TenantInvitationDetailsApi(APIView):
    @extend_schema(responses={200: TenantInvitationSerializer}, summary="Check invitation")
    def get(self, request: Request, tenant_id: int, token: str) -> Response:
        invitation = get_object_or_404(TenantInvitation, tenant_id=tenant_id, token=token)
        response_data = TenantInvitationSerializer(invitation).data
        return Response(response_data, status=200)


class TenantInvitationAcceptApi(APIView):
    @extend_schema(responses={204: None}, summary="Accept invitation")
    def post(self, request: Request, tenant_id: int, token: str) -> Response:
        invitation = get_object_or_404(TenantInvitation, tenant_id=tenant_id, token=token)
        accept_tenant_invitation(invitation)

        return Response(status=204)


class TenantInvitationSignupApi(APIView):
    @extend_schema(
        request=TenantInvitationSignupSerializer, responses={200: MeSerializer}, summary="Sign up from invitation"
    )
    def post(self, request: Request, tenant_id: int, token: str) -> Response:
        serializer = TenantInvitationSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = get_object_or_404(TenantInvitation, tenant_id=tenant_id, token=token)
        tenant_user = signup_user(invitation=invitation, **serializer.validated_data)

        response_data = MeSerializer(tenant_user.user).data
        return Response(response_data, status=201)


class PasswordChangeApi(TenantUserMixin, APIView):
    permission_classes = [IsTenantUser]

    def get_object(self) -> User:
        return self.tenant_user.user

    @extend_schema(request=PasswordChangeSerializer, responses={204: None}, summary="Change password")
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_user_password(request=request, user=self.tenant_user.user, **serializer.validated_data)

        return Response(status=204)


class PasswordResetApi(TenantMixin, APIView):
    @extend_schema(request=PasswordResetSerializer, responses={204: None}, summary="Reset password")
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_password(tenant=self.tenant, **serializer.validated_data)

        return Response(status=204)


class PasswordResetValidateTokenApi(TenantMixin, APIView):
    @extend_schema(responses={204: None}, summary="Validate password reset token")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        try:
            decode_password_reset_token(
                uid=kwargs['uid'],
                token=kwargs['token'],
            )
        except ValidationError:
            return Response(status=404)

        return Response(status=204)


class PasswordResetPasswordChangeApi(TenantMixin, APIView):
    @extend_schema(request=PasswordResetChangePasswordSerializer, responses={204: None}, summary="Set a new password")
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = PasswordResetChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_password_reset_password(uid=kwargs['uid'], token=kwargs['token'], **serializer.validated_data)
        return Response(status=204)


class MeAvatarUpdateApi(TenantUserMixin, APIView):
    permission_classes = [IsTenantUser]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {'profile_image': {'type': 'string', 'format': 'binary'}},
            }
        },
        responses={200: MeSerializer},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = MeAvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_user_avatar(self.tenant_user.user, **serializer.validated_data)

        self.tenant_user.refresh_from_db()
        response_data = MeSerializer(self.tenant_user.user).data
        return Response(response_data, status=200)


class MeAvatarDeleteApi(TenantUserMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={204: None},
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        update_user_avatar(self.tenant_user.user, None)
        return Response(status=204)
