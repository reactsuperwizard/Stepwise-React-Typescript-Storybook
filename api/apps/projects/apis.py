import logging
from typing import cast

from django.db import models
from django.db.models import Prefetch
from django.utils.functional import cached_property
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import CustomFilterMixin
from apps.emps.serializers import CreateUpdateEMPSerializer, EMPSerializer
from apps.emps.services import create_emp, delete_emp, update_emp
from apps.projects.filters import ProjectRigListFilter
from apps.projects.models import Plan, Project
from apps.projects.serializers import (
    CreateUpdatePlanSerializer,
    CreateUpdateProjectSerializer,
    ElementListSerializer,
    PlanDetailsSerializer,
    PlanListSerializer,
    ProjectDetailsSerializer,
    ProjectListSerializer,
)
from apps.projects.services import create_plan, create_project, delete_project, update_plan, update_project
from apps.rigs.models import (
    CustomDrillship,
    CustomDrillshipQuerySet,
    CustomJackupRig,
    CustomJackupRigQuerySet,
    CustomSemiRig,
    CustomSemiRigQuerySet,
    RigType,
)
from apps.rigs.serializers import CustomRigListSerializer
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser
from apps.wells.models import CustomWell
from apps.wells.serializers import CustomWellListSerializer

logger = logging.getLogger(__name__)


class ProjectListApi(TenantMixin, CustomFilterMixin, ListAPIView):
    queryset = Project.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = ProjectListSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self) -> models.QuerySet:
        return Project.objects.filter(tenant=self.tenant)

    @extend_schema(summary="Project list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CreateProjectApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdateProjectSerializer, responses={201: ProjectDetailsSerializer}, summary="Create project"
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateUpdateProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project(tenant=self.tenant, user=cast(User, self.request.user), **serializer.validated_data)
        return Response(ProjectDetailsSerializer(project).data, status=201)


class ProjectMixin(TenantMixin):
    @cached_property
    def project(self):
        return get_object_or_404(Project.objects.filter(tenant=self.tenant), pk=self.kwargs['project_id'])


class UpdateProjectApi(ProjectMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdateProjectSerializer, responses={200: ProjectDetailsSerializer}, summary="Update project"
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateUpdateProjectSerializer(instance=self.project, data=request.data)
        serializer.is_valid(raise_exception=True)
        project = update_project(project=self.project, user=cast(User, self.request.user), **serializer.validated_data)
        return Response(ProjectDetailsSerializer(project).data, status=200)


class ProjectDetailsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: ProjectDetailsSerializer}, summary="Project details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant).prefetch_related(
                Prefetch('semi_rigs', queryset=CustomSemiRig.objects.with_type()),  # type: ignore
                Prefetch('jackup_rigs', queryset=CustomJackupRig.objects.with_type()),  # type: ignore
            ),
            pk=self.kwargs['project_id'],
        )
        serializer = ProjectDetailsSerializer(instance=project)
        return Response(serializer.data, status=200)


class DeleteProjectApi(ProjectMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete project")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        delete_project(user=cast(User, request.user), project=self.project)

        return Response(status=204)


class ProjectRigListApi(TenantMixin, CustomFilterMixin, ListAPIView):
    queryset = CustomSemiRig.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = CustomRigListSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    pagination_class = None
    filterset_class = ProjectRigListFilter

    def get_queryset(self) -> models.QuerySet:
        values = ('id', 'name', 'type', 'created_at', 'updated_at', 'draft', 'project_id', 'emp_id')
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant).prefetch_related(
                Prefetch('semi_rigs', queryset=CustomSemiRig.objects.with_type()),  # type: ignore
                Prefetch('jackup_rigs', queryset=CustomJackupRig.objects.with_type()),  # type: ignore
                Prefetch('drillships', queryset=CustomDrillship.objects.with_type()),  # type: ignore
            ),
            pk=self.kwargs['project_id'],
        )
        semi_rigs = self.custom_filter_queryset(
            queryset=project.semi_rigs.all(), filter_backends=[DjangoFilterBackend]
        ).values(*values)
        jackup_rigs = self.custom_filter_queryset(
            queryset=project.jackup_rigs.all(), filter_backends=[DjangoFilterBackend]
        ).values(*values)
        drillships = self.custom_filter_queryset(
            queryset=project.drillships.all(), filter_backends=[DjangoFilterBackend]
        ).values(*values)
        return self.custom_filter_queryset(
            queryset=semi_rigs.union(jackup_rigs).union(drillships), filter_backends=[filters.OrderingFilter]
        )

    @extend_schema(summary="Project rig list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProjectWellListApi(TenantMixin, ListAPIView):
    queryset = CustomWell.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = CustomWellListSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name']
    filterset_fields = ['draft']
    pagination_class = None

    def get_queryset(self) -> models.QuerySet[CustomWell]:
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant).prefetch_related(
                Prefetch('wells', queryset=CustomWell.objects.select_related('project'))
            ),
            pk=self.kwargs['project_id'],
        )
        return project.wells.order_by('-created_at')

    @extend_schema(summary="Project well list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ProjectPlanListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = PlanListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'name']
    pagination_class = None

    def get_queryset(self) -> models.QuerySet[Plan]:
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant).prefetch_related('plans__plan_wells'),
            pk=self.kwargs['project_id'],
        )
        return project.plans.order_by('-created_at')

    @extend_schema(summary="Project plan list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ProjectPlanDetailsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: PlanDetailsSerializer}, summary="Plan details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        plan = get_object_or_404(
            Plan.objects.filter(
                project_id=self.kwargs['project_id'], project__tenant=self.tenant, pk=self.kwargs['plan_id']
            )
            .select_related('reference_operation_jackup', 'reference_operation_semi', 'reference_operation_drillship')
            .prefetch_related('plan_wells'),
        )
        serializer = PlanDetailsSerializer(instance=plan)
        return Response(serializer.data, status=200)


class CreateProjectPlanApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdatePlanSerializer, responses={201: PlanDetailsSerializer}, summary="Create project plan"
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        project = get_object_or_404(
            Project.objects.filter(tenant=self.tenant),
            pk=self.kwargs['project_id'],
        )
        serializer = CreateUpdatePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = create_plan(user=cast(User, self.request.user), project=project, **serializer.validated_data)

        response_data = PlanDetailsSerializer(plan).data
        return Response(response_data, status=201)


class DeleteProjectPlanApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete project plan")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        plan_id = self.kwargs['plan_id']

        logger.info(f'User(pk={request.user.pk}) is deleting Plan(pk={plan_id})')

        plan = get_object_or_404(
            Plan.objects.filter(project__tenant=self.tenant), project__pk=self.kwargs['project_id'], pk=plan_id
        )
        plan.delete()

        logger.info(f'Plan(pk={plan_id}) has been deleted')
        return Response(status=204)


class UpdateProjectPlanApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateUpdatePlanSerializer, responses={200: PlanDetailsSerializer}, summary="Update project plan"
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        plan = get_object_or_404(
            Plan.objects.filter(project__tenant=self.tenant, project__pk=self.kwargs["project_id"]),
            pk=self.kwargs['plan_id'],
        )
        serializer = CreateUpdatePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = update_plan(user=cast(User, self.request.user), plan=plan, **serializer.validated_data)

        response_data = PlanDetailsSerializer(plan).data
        return Response(response_data, status=200)


class ProjectRigEmpMixin(ProjectMixin):
    def get_rigs(self) -> CustomJackupRigQuerySet | CustomSemiRigQuerySet | CustomDrillshipQuerySet:
        rig_type = self.kwargs['rig_type'].upper()
        match rig_type:
            case RigType.SEMI:
                return cast(CustomSemiRigQuerySet, self.project.semi_rigs.all())
            case RigType.JACKUP:
                return cast(CustomJackupRigQuerySet, self.project.jackup_rigs.all())
            case RigType.DRILLSHIP:
                return cast(CustomDrillshipQuerySet, self.project.drillships.all())
            case _:
                raise NotImplementedError(f'Unknown rig type: {self.kwargs["rig_type"]}')


class ProjectRigEmpDetailsApi(ProjectRigEmpMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: EMPSerializer}, summary="Retrieve project rig emp details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(
            self.get_rigs().filter(emp__isnull=False).select_related("emp"), pk=self.kwargs["rig_id"]
        )

        response_data = EMPSerializer(rig.emp).data
        return Response(response_data, status=200)


class CreateProjectRigEmpApi(ProjectRigEmpMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(request=CreateUpdateEMPSerializer, responses={201: EMPSerializer}, summary="Create project rig emp")
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(self.get_rigs(), pk=self.kwargs["rig_id"])

        serializer = CreateUpdateEMPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emp = create_emp(user=cast(User, request.user), custom_rig=rig, **serializer.validated_data)

        response_data = EMPSerializer(emp).data
        return Response(response_data, status=201)


class UpdateProjectRigEmpApi(ProjectRigEmpMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(request=CreateUpdateEMPSerializer, responses={200: EMPSerializer}, summary="Update project rig emp")
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(
            self.get_rigs().filter(emp__isnull=False).select_related('emp'), pk=self.kwargs["rig_id"]
        )

        serializer = CreateUpdateEMPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emp = update_emp(user=cast(User, request.user), emp=rig.emp, **serializer.validated_data)

        response_data = EMPSerializer(emp).data
        return Response(response_data, status=200)


class DeleteProjectRigEmpApi(ProjectRigEmpMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete project rig emp")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        rig = get_object_or_404(
            self.get_rigs().filter(emp__isnull=False).select_related('emp'), pk=self.kwargs["rig_id"]
        )

        delete_emp(user=cast(User, request.user), emp=rig.emp)
        return Response(status=204)


class ElementListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = ElementListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'name']

    def get_queryset(self) -> models.QuerySet:
        values = ('id', 'name', 'element_type', 'created_at', 'updated_at', 'project')

        custom_semi_rigs = (
            CustomSemiRig.objects.filter(tenant=self.tenant).with_element_type().values(*values)  # type: ignore
        )
        custom_jackup_rigs = (
            CustomJackupRig.objects.filter(tenant=self.tenant).with_element_type().values(*values)  # type: ignore
        )
        custom_drillships = (
            CustomDrillship.objects.filter(tenant=self.tenant).with_element_type().values(*values)  # type: ignore
        )
        custom_wells = CustomWell.objects.filter(tenant=self.tenant).with_element_type().values(*values)  # type: ignore

        return cast(
            models.QuerySet,
            custom_semi_rigs.union(custom_jackup_rigs)
            .union(custom_drillships)
            .union(custom_wells)
            .order_by('-created_at'),
        )

    @extend_schema(summary="Element list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)
