from typing import cast

from django.contrib.auth import logout
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.privacy.models import PrivacyPolicy, PrivacyPolicyConsent
from apps.privacy.serializers import PrivacyPolicyConsentSerializer, PrivacyPolicySerializer
from apps.privacy.services import accept_active_policy, create_delete_account_request
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser


class PrivacyPolicyDetailsApi(APIView):
    @extend_schema(responses={200: PrivacyPolicySerializer}, summary="Policy details")
    def get(self, _: Request, policy_id: int) -> Response:
        policy = get_object_or_404(PrivacyPolicy, pk=policy_id)

        response_data = PrivacyPolicySerializer(policy).data
        return Response(response_data, status=200)


class PrivacyPolicyLatestApi(APIView):
    @extend_schema(responses={200: PrivacyPolicySerializer}, summary="Latest policy details")
    def get(self, _: Request) -> Response:
        policy = get_object_or_404(PrivacyPolicy, is_active=True)

        response_data = PrivacyPolicySerializer(policy).data
        return Response(response_data, status=200)


class PrivacyPolicyLatestAcceptApi(APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Latest policy accept")
    def post(self, request: Request, tenant_id: int) -> Response:
        user = cast(User, request.user)
        try:
            accept_active_policy(user)
        except PrivacyPolicy.DoesNotExist:
            raise Http404()

        return Response(status=204)


class PrivacyPolicyConsentLatestApi(APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: PrivacyPolicyConsentSerializer}, summary="Latest consent details")
    def get(self, request: Request, tenant_id: int) -> Response:
        user = cast(User, request.user)
        consent = PrivacyPolicyConsent.objects.filter(user=user).order_by('created_at').last()

        if consent is None:
            raise Http404()

        response_data = PrivacyPolicyConsentSerializer(consent).data
        return Response(response_data, status=200)


class PrivacyPolicyConsentListApi(APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: PrivacyPolicyConsentSerializer(many=True)}, summary="Consent list")
    def get(self, request: Request, tenant_id: int) -> Response:
        user = cast(User, request.user)
        qs = PrivacyPolicyConsent.objects.filter(user=user)
        response_data = PrivacyPolicyConsentSerializer(qs, many=True).data
        return Response(response_data, status=200)


class DeleteAccountApi(APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete account")
    def delete(self, request: Request, tenant_id: int) -> Response:
        user = cast(User, request.user)
        create_delete_account_request(user)
        logout(request)
        return Response(status=204)
