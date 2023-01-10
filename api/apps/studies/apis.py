from typing import cast

from django.db import models
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.studies.models import (
    StudyElement,
    StudyElementDrillshipRelation,
    StudyElementJackupRigRelation,
    StudyElementSemiRigRelation,
    StudyMetric,
)
from apps.studies.serializers import (
    CreateUpdateStudyElementSerializer,
    StudyElementListSerializer,
    StudyElementSerializer,
    StudyMetricSerializer,
    SwappedStudyElementsSerializer,
    SwapStudyElementsSerializer,
)
from apps.studies.services import create_study_element, delete_study_element, swap_study_elements, update_study_element
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser


class StudyElementDetailsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: StudyElementSerializer},
        summary="Study element details",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        study_element = get_object_or_404(
            StudyElement.objects.filter(
                project__tenant__pk=self.kwargs["tenant_id"],
                project__pk=self.kwargs["project_id"],
            )
            .select_related('metric')
            .prefetch_related(
                Prefetch(
                    'studyelementsemirigrelation_set',
                    queryset=StudyElementSemiRigRelation.objects.select_related('rig'),
                ),
                Prefetch(
                    'studyelementjackuprigrelation_set',
                    queryset=StudyElementJackupRigRelation.objects.select_related('rig'),
                ),
                Prefetch(
                    'studyelementdrillshiprelation_set',
                    queryset=StudyElementDrillshipRelation.objects.select_related('rig'),
                ),
            )
            .order_by('order'),
            pk=self.kwargs["element_id"],
        )

        response_data = StudyElementSerializer(study_element).data
        return Response(response_data, status=200)


class StudyElementListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = StudyElementListSerializer
    pagination_class = None

    def get_queryset(self) -> models.QuerySet[StudyElement]:
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant),
            pk=self.kwargs['project_id'],
        )
        return StudyElement.objects.filter(project=project).select_related('metric').order_by('order')

    @extend_schema(summary="Study element list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class StudyMetricListApi(ListAPIView):
    queryset = StudyMetric.objects.all().order_by('id')
    permission_classes = [IsTenantUser]
    serializer_class = StudyMetricSerializer
    pagination_class = None

    @extend_schema(summary="Study metric list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class DeleteStudyElementApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete study element")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        study_element = get_object_or_404(
            StudyElement.objects.filter(project__tenant=self.tenant, project_id=self.kwargs['project_id']),
            pk=self.kwargs['element_id'],
        )

        delete_study_element(user=cast(User, self.request.user), study_element=study_element)

        return Response(status=204)


class CreateStudyElementApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdateStudyElementSerializer,
        responses={201: StudyElementListSerializer},
        summary="Create study element",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        project = get_object_or_404(Project.objects.filter(tenant=self.tenant), pk=self.kwargs['project_id'])
        serializer = CreateUpdateStudyElementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        study_element = create_study_element(
            user=cast(User, self.request.user), project=project, **serializer.validated_data
        )

        return Response(StudyElementListSerializer(study_element).data, status=201)


class UpdateStudyElementApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdateStudyElementSerializer,
        responses={200: StudyElementListSerializer},
        summary="Update study element",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        study_element = get_object_or_404(
            StudyElement.objects.filter(project__tenant=self.tenant, project_id=self.kwargs['project_id']),
            pk=self.kwargs['element_id'],
        )
        serializer = CreateUpdateStudyElementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        study_element = update_study_element(
            user=cast(User, self.request.user), study_element=study_element, **serializer.validated_data
        )

        return Response(StudyElementListSerializer(study_element).data)


class SwapStudyElementsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=SwapStudyElementsSerializer,
        responses={200: SwappedStudyElementsSerializer},
        summary="Swap study elements",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        project = get_object_or_404(Project.objects.filter(tenant=self.tenant), pk=self.kwargs['project_id'])
        serializer = SwapStudyElementsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        first_element, second_element = swap_study_elements(
            user=cast(User, self.request.user), project=project, **serializer.validated_data
        )

        return Response(
            SwappedStudyElementsSerializer({"first_element": first_element, "second_element": second_element}).data
        )
