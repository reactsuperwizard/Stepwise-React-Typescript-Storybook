import logging
from typing import cast

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import CustomFilterMixin, DraftMixin
from apps.rigs.filters import CustomRigListFilter
from apps.rigs.models import (
    ConceptDrillship,
    ConceptJackupRig,
    ConceptSemiRig,
    CustomDrillship,
    CustomJackupRig,
    CustomSemiRig,
)
from apps.rigs.serializers import (
    ConceptDrillshipDetailsSerializer,
    ConceptJackupRigDetailsSerializer,
    ConceptSemiRigDetailsSerializer,
    CreateCustomDrillshipSerializerFactory,
    CreateCustomJackupRigSerializerFactory,
    CreateCustomSemiRigSerializerFactory,
    CustomDrillshipDetailsSerializer,
    CustomJackupRigDetailsSerializer,
    CustomRigListSerializer,
    CustomSemiRigDetailsSerializer,
    RigListSerializer,
    UpdateCustomDrillshipSerializerFactory,
    UpdateCustomJackupRigSerializerFactory,
    UpdateCustomSemiRigSerializerFactory,
)
from apps.rigs.services.apis import (
    create_custom_drillship,
    create_custom_jackup_rig,
    create_custom_semi_rig,
    delete_custom_drillship,
    delete_custom_jackup_rig,
    delete_custom_semi_rig,
    update_custom_drillship,
    update_custom_jackup_rig,
    update_custom_semi_rig,
)
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser

logger = logging.getLogger(__name__)


class CustomRigListApi(TenantMixin, CustomFilterMixin, ListAPIView):
    queryset = CustomSemiRig.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = CustomRigListSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name']
    filterset_class = CustomRigListFilter
    ordering = ['-created_at']

    def get_queryset(self) -> models.QuerySet:
        values = (
            'id',
            'name',
            'type',
            'created_at',
            'updated_at',
            'draft',
            'project_id',
            'emp_id',
        )

        custom_semi_rigs = self.custom_filter_queryset(
            queryset=CustomSemiRig.objects.filter(tenant=self.tenant).with_type().values(*values),  # type: ignore
            filter_backends=[DjangoFilterBackend],
        )
        custom_jackup_rigs = self.custom_filter_queryset(
            queryset=CustomJackupRig.objects.filter(tenant=self.tenant).with_type().values(*values),  # type: ignore
            filter_backends=[DjangoFilterBackend],
        )
        custom_drillships = self.custom_filter_queryset(
            queryset=CustomDrillship.objects.filter(tenant=self.tenant).with_type().values(*values),  # type: ignore
            filter_backends=[DjangoFilterBackend],
        )

        return self.custom_filter_queryset(
            queryset=custom_semi_rigs.union(custom_jackup_rigs).union(custom_drillships),
            filter_backends=[filters.OrderingFilter],
        )

    @extend_schema(summary="Custom rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class CustomJackupRigDetailsApi(TenantMixin, RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = CustomJackupRigDetailsSerializer
    lookup_url_kwarg = 'rig_id'

    def get_queryset(self):
        return CustomJackupRig.objects.filter(tenant=self.tenant)

    @extend_schema(summary="Custom jackup rig details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CreateCustomJackupRigApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateCustomJackupRigSerializerFactory(True),
        summary="Create custom jackup rig",
        responses={201: CustomJackupRigDetailsSerializer},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateCustomJackupRigSerializerFactory(self.is_draft)(data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = create_custom_jackup_rig(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomJackupRigDetailsSerializer(rig).data, status=201)


class UpdateCustomJackupRigApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateCustomJackupRigSerializerFactory(True),
        summary="Update custom jackup rig",
        responses={200: CustomJackupRigDetailsSerializer},
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        instance = get_object_or_404(CustomJackupRig.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])
        serializer = UpdateCustomJackupRigSerializerFactory(self.is_draft)(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = update_custom_jackup_rig(rig=instance, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomJackupRigDetailsSerializer(rig).data, status=200)


class CustomSemiRigDetailsApi(TenantMixin, RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = CustomSemiRigDetailsSerializer
    lookup_url_kwarg = 'rig_id'

    def get_queryset(self) -> models.QuerySet["CustomSemiRig"]:
        return CustomSemiRig.objects.filter(tenant=self.tenant)

    @extend_schema(summary="Custom semi rig details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CreateCustomSemiRigApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateCustomSemiRigSerializerFactory(True),
        summary="Create custom semi rig",
        responses={201: CustomSemiRigDetailsSerializer},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateCustomSemiRigSerializerFactory(self.is_draft)(data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = create_custom_semi_rig(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomSemiRigDetailsSerializer(rig).data, status=201)


class UpdateCustomSemiRigApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateCustomSemiRigSerializerFactory(True),
        summary="Update custom semi rig",
        responses={200: CustomSemiRigDetailsSerializer},
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        instance = get_object_or_404(CustomSemiRig.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])
        serializer = UpdateCustomSemiRigSerializerFactory(self.is_draft)(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = update_custom_semi_rig(rig=instance, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomSemiRigDetailsSerializer(rig).data, status=200)


class ConceptJackupRigDetailsApi(RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = ConceptJackupRigDetailsSerializer
    lookup_url_kwarg = 'rig_id'
    queryset = ConceptJackupRig.objects.all()

    @extend_schema(summary="Concept jackup rig details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptSemiRigDetailsApi(RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = ConceptSemiRigDetailsSerializer
    lookup_url_kwarg = 'rig_id'
    queryset = ConceptSemiRig.objects.all()

    @extend_schema(summary="Concept semi rig details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CustomJackupRigListApi(TenantMixin, ListAPIView):
    queryset = CustomJackupRig.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['draft']

    def get_queryset(self) -> models.QuerySet['CustomJackupRig']:
        return CustomJackupRig.objects.filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Custom jackup rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CustomSemiRigListApi(TenantMixin, ListAPIView):
    queryset = CustomSemiRig.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['draft']

    def get_queryset(self) -> models.QuerySet['CustomSemiRig']:
        return CustomSemiRig.objects.filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Custom semi rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptJackupRigListApi(ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    queryset = ConceptJackupRig.objects.all().order_by('-created_at')

    @extend_schema(summary="Concept jackup rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptSemiRigListApi(ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    queryset = ConceptSemiRig.objects.all().order_by('-created_at')

    @extend_schema(summary="Concept semi rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class DeleteCustomJackupRigApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete custom jackup rig")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(CustomJackupRig.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])

        delete_custom_jackup_rig(user=cast(User, self.request.user), rig=rig)

        return Response(status=204)


class DeleteCustomSemiRigApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete custom semi rig")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(CustomSemiRig.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])

        delete_custom_semi_rig(user=cast(User, self.request.user), rig=rig)

        return Response(status=204)


class CustomDrillshipListApi(TenantMixin, ListAPIView):
    queryset = CustomDrillship.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['draft']

    def get_queryset(self) -> models.QuerySet['CustomDrillship']:
        return CustomDrillship.objects.filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Custom drillship list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptDrillshipListApi(ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = RigListSerializer
    queryset = ConceptDrillship.objects.all().order_by('-created_at')

    @extend_schema(summary="Concept drillship list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CreateCustomDrillshipApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateCustomDrillshipSerializerFactory(True),
        summary="Create custom drillship",
        responses={201: CustomDrillshipDetailsSerializer},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateCustomDrillshipSerializerFactory(self.is_draft)(data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = create_custom_drillship(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomDrillshipDetailsSerializer(rig).data, status=201)


class UpdateCustomDrillshipApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateCustomDrillshipSerializerFactory(True),
        summary="Update custom drillship",
        responses={200: CustomDrillshipDetailsSerializer},
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        instance = get_object_or_404(CustomDrillship.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])
        serializer = UpdateCustomDrillshipSerializerFactory(self.is_draft)(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        rig = update_custom_drillship(rig=instance, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomDrillshipDetailsSerializer(rig).data, status=200)


class CustomDrillshipDetailsApi(TenantMixin, RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = CustomDrillshipDetailsSerializer
    lookup_url_kwarg = 'rig_id'

    def get_queryset(self) -> models.QuerySet['CustomDrillship']:
        return CustomDrillship.objects.filter(tenant=self.tenant)

    @extend_schema(summary="Custom drillship details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptDrillshipDetailsApi(RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = ConceptDrillshipDetailsSerializer
    lookup_url_kwarg = 'rig_id'
    queryset = ConceptDrillship.objects.all()

    @extend_schema(summary="Concept drillship details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class DeleteCustomDrillshipApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete custom drillship")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(CustomDrillship.objects.filter(tenant=self.tenant), pk=self.kwargs['rig_id'])

        delete_custom_drillship(user=cast(User, self.request.user), rig=rig)

        return Response(status=204)
