import logging
from typing import cast

from django.db import models
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import DraftMixin
from apps.emissions.models import BaselineInput, CustomMode, CustomPhase
from apps.emissions.serializers import EmissionReductionInitiativeListSerializer
from apps.monitors.models import MonitorFunctionType
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsTenantUser
from apps.wells.filters import CustomWellListFilter
from apps.wells.mixins import WellPlannerMixin
from apps.wells.models import ConceptWell, CustomWell, WellPlanner, WellReferenceMaterial
from apps.wells.serializers import (
    ApproveWellPlannerCompleteHelicopterUsesSerializer,
    ApproveWellPlannerCompleteStepsSerializer,
    ApproveWellPlannerCompleteVesselUsesSerializer,
    ConceptWellDetailsSerializer,
    ConceptWellListSerializer,
    CreateCustomWellSerializerFactory,
    CreateWellPlannerCompleteStepSerializer,
    CreateWellPlannerPlannedStepSerializer,
    CustomWellDetailsSerializer,
    CustomWellListSerializer,
    MoveWellPlannerStepSerializer,
    StartEndDateParametersSerializer,
    UpdateCustomWellSerializerFactory,
    UpdateWellPlannerActualStartDateSerializer,
    UpdateWellPlannerCompleteStepSerializer,
    UpdateWellPlannerEmissionReductionInitiativesSerializer,
    UpdateWellPlannerPlannedStepSerializer,
    WellPlannerCO2DatasetSerializer,
    WellPlannerCO2SavedDatasetSerializer,
    WellPlannerCompleteSummarySerializer,
    WellPlannerDetailsSerializer,
    WellPlannerListSerializer,
    WellPlannerMeasurementDatasetSerializer,
    WellPlannerModeListSerializer,
    WellPlannerPhaseListSerializer,
    WellPlannerPlannedStepCO2Serializer,
    WellPlannerSummarySerializer,
    WellReferenceMaterialSerializer,
)
from apps.wells.services.api import (
    approve_well_planner_complete_helicopter_uses,
    approve_well_planner_complete_steps,
    approve_well_planner_complete_vessel_uses,
    available_emission_reduction_initiatives,
    complete_well_planner_planning,
    complete_well_planner_reviewing,
    create_custom_well,
    create_well_planner_complete_step,
    create_well_planner_planned_step,
    delete_custom_well,
    delete_well_planner_complete_step,
    delete_well_planner_planned_step,
    duplicate_well_planner_complete_step,
    duplicate_well_planner_planned_step,
    get_well_planner_measured_co2_dataset,
    get_well_planner_measured_summary,
    get_well_planner_measurement_dataset,
    get_well_planner_planned_co2_dataset,
    get_well_planner_planned_step_co2,
    get_well_planner_saved_co2_dataset,
    get_well_planner_summary,
    move_well_planner_complete_step,
    move_well_planner_planned_step,
    update_custom_well,
    update_well_planner_actual_start_date,
    update_well_planner_complete_step,
    update_well_planner_complete_step_emission_reduction_initiatives,
    update_well_planner_planned_step,
    update_well_planner_planned_step_emission_reduction_initiatives,
)

logger = logging.getLogger(__name__)


class CustomWellListApi(TenantMixin, ListAPIView):
    queryset = CustomWell.objects.none()  # needed for drf spectacular documentation
    permission_classes = [IsTenantUser]
    serializer_class = CustomWellListSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'name']
    filterset_class = CustomWellListFilter

    def get_queryset(self) -> models.QuerySet['CustomWell']:
        return CustomWell.objects.filter(tenant=self.tenant).select_related('project').order_by('-created_at')

    @extend_schema(summary="Custom well list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class ConceptWellListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    queryset = ConceptWell.objects.all().order_by('-created_at')
    serializer_class = ConceptWellListSerializer

    @extend_schema(summary="Concept well list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CreateCustomWellApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateCustomWellSerializerFactory(True),
        summary="Create custom well",
        responses={201: CustomWellDetailsSerializer},
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateCustomWellSerializerFactory(self.is_draft)(data=request.data)
        serializer.is_valid(raise_exception=True)
        well = create_custom_well(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomWellDetailsSerializer(well).data, status=201)


class UpdateCustomWellApi(DraftMixin, TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateCustomWellSerializerFactory(True),
        summary="Update custom well",
        responses={200: CustomWellDetailsSerializer},
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        instance = get_object_or_404(CustomWell.objects.filter(tenant=self.tenant), pk=self.kwargs['well_id'])
        serializer = UpdateCustomWellSerializerFactory(self.is_draft)(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        well = update_custom_well(well=instance, user=cast(User, request.user), **serializer.validated_data)
        return Response(CustomWellDetailsSerializer(well).data, status=200)


class ConceptWellDetailsApi(RetrieveAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = ConceptWellDetailsSerializer
    lookup_url_kwarg = 'well_id'
    queryset = ConceptWell.objects.all()

    @extend_schema(summary="Concept well details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CustomWellDetailsApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        summary="Custom well details",
        responses={200: CustomWellDetailsSerializer},
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        object = get_object_or_404(CustomWell.objects.filter(tenant=self.tenant), pk=self.kwargs['well_id'])
        return Response(CustomWellDetailsSerializer(object).data)


class DeleteCustomWellApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={204: None}, summary="Delete custom well")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        well = get_object_or_404(CustomWell.objects.filter(tenant=self.tenant), pk=self.kwargs['well_id'])
        delete_custom_well(well, cast(User, request.user))
        return Response(status=204)


class WellPlannerDetailsApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: WellPlannerDetailsSerializer}, summary="Get well planner details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class CompleteWellPlannerPlannedApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: WellPlannerDetailsSerializer}, summary='Complete well planner planned')
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        completed_well_planner = complete_well_planner_planning(
            well_planner=self.well_planner,
            user=cast(User, request.user),
        )

        response_data = WellPlannerDetailsSerializer(completed_well_planner).data
        return Response(response_data, status=200)


class CreateWellPlannerPlannedStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateWellPlannerPlannedStepSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well planner planned step",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = CreateWellPlannerPlannedStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_well_planner_planned_step(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=201)


class UpdateWellPlannerPlannedStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateWellPlannerPlannedStepSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planner planned step",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        planned_step = get_object_or_404(
            self.well_planner.planned_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_planned_step_id'],
        )

        serializer = UpdateWellPlannerPlannedStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planner_planned_step(
            planned_step=planned_step, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class DeleteWellPlannerPlannedStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={204: None},
        summary="Delete well planner planned step",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        planned_step = get_object_or_404(
            self.well_planner.planned_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_planned_step_id'],
        )

        delete_well_planner_planned_step(planned_step=planned_step, user=cast(User, request.user))

        return Response(status=204)


class WellPlannerPlannedCo2Api(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerCO2DatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner planned CO2 dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        parameters_serializer = StartEndDateParametersSerializer(data=request.GET)
        parameters_serializer.is_valid(raise_exception=True)

        dataset = get_well_planner_planned_co2_dataset(
            well_planner=self.well_planner, improved=True, **parameters_serializer.validated_data
        )
        response_data = WellPlannerCO2DatasetSerializer(dataset, many=True).data

        return Response(response_data, status=200)


class WellPlannerPlannedCo2SavedApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerCO2SavedDatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner planned CO2 saved dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        parameters_serializer = StartEndDateParametersSerializer(data=request.GET)
        parameters_serializer.is_valid(raise_exception=True)

        dataset = get_well_planner_saved_co2_dataset(
            well_planner=self.well_planner, **parameters_serializer.validated_data
        )

        response_data = WellPlannerCO2SavedDatasetSerializer(dataset, many=True).data
        return Response(response_data, status=200)


class WellPlannerPlannedSummaryApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerSummarySerializer},
        summary="Get well planner planned summary",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        summary = get_well_planner_summary(self.well_planner)

        response_data = WellPlannerSummarySerializer(summary).data
        return Response(response_data, status=200)


class CreateWellPlannerCompleteStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=CreateWellPlannerCompleteStepSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well planner complete step",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = CreateWellPlannerCompleteStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_well_planner_complete_step(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=201)


class UpdateWellPlannerCompleteStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateWellPlannerCompleteStepSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planner complete step",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        complete_step = get_object_or_404(
            self.well_planner.complete_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_complete_step_id'],
        )

        serializer = UpdateWellPlannerCompleteStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planner_complete_step(
            complete_step=complete_step, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class DeleteWellPlannerCompleteStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={204: None},
        summary="Delete well planner complete step",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        complete_step = get_object_or_404(
            self.well_planner.complete_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_complete_step_id'],
        )

        delete_well_planner_complete_step(complete_step=complete_step, user=cast(User, request.user))

        return Response(status=204)


class ApproveWellPlannerCompleteStepsApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=ApproveWellPlannerCompleteStepsSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Approve well planner complete steps",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = ApproveWellPlannerCompleteStepsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approve_well_planner_complete_steps(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class CompleteWellPlannerCompleteApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Complete well planner complete",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        completed_well_planner = complete_well_planner_reviewing(
            well_planner=well_planner, user=cast(User, request.user)
        )

        response_data = WellPlannerDetailsSerializer(completed_well_planner).data
        return Response(response_data, status=200)


class WellPlannerCompleteSummaryApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerCompleteSummarySerializer},
        summary="Get well planner complete summary",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        summary = get_well_planner_measured_summary(well_planner=self.well_planner)

        response_data = WellPlannerCompleteSummarySerializer(summary).data
        return Response(response_data, status=200)


class WellPlannerMeasuredCo2Api(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerCO2DatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner measured CO2 dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        parameters_serializer = StartEndDateParametersSerializer(data=request.GET)
        parameters_serializer.is_valid(raise_exception=True)

        dataset = get_well_planner_measured_co2_dataset(
            well_planner=self.well_planner, **parameters_serializer.validated_data
        )

        response_data = WellPlannerCO2DatasetSerializer(dataset, many=True).data
        return Response(response_data, status=200)


class BaseWellPlannerMeasurementApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]
    MONITOR_FUNCTION_TYPE: MonitorFunctionType

    def __init__(self, *args, **kwargs):
        assert self.MONITOR_FUNCTION_TYPE is not None, "MONITOR_FUNCTION_TYPE must be set"
        super().__init__(*args, **kwargs)

    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        parameters_serializer = StartEndDateParametersSerializer(data=request.GET)
        parameters_serializer.is_valid(raise_exception=True)

        dataset = get_well_planner_measurement_dataset(
            well_planner=self.well_planner,
            monitor_function_type=self.MONITOR_FUNCTION_TYPE,
            **parameters_serializer.validated_data,
        )

        response_data = WellPlannerMeasurementDatasetSerializer(dataset, many=True).data
        return Response(response_data, status=200)


class WellPlannerMeasuredWindSpeedApi(BaseWellPlannerMeasurementApi):
    MONITOR_FUNCTION_TYPE = MonitorFunctionType.WIND_SPEED

    @extend_schema(
        responses={200: WellPlannerMeasurementDatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner measured wind speed dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class WellPlannerMeasuredAirTemperatureApi(BaseWellPlannerMeasurementApi):
    MONITOR_FUNCTION_TYPE = MonitorFunctionType.AIR_TEMPERATURE

    @extend_schema(
        responses={200: WellPlannerMeasurementDatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner measured air temperature dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class WellPlannerMeasuredWaveHeaveApi(BaseWellPlannerMeasurementApi):
    MONITOR_FUNCTION_TYPE = MonitorFunctionType.WAVE_HEAVE

    @extend_schema(
        responses={200: WellPlannerMeasurementDatasetSerializer(many=True)},
        parameters=[StartEndDateParametersSerializer],
        summary="Get well planner measured wave heave dataset",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class DuplicateWellPlannerPlannedStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Duplicate well planner planned step",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        planned_step = get_object_or_404(
            self.well_planner.planned_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_planned_step_id'],
        )

        duplicate_well_planner_planned_step(planned_step=planned_step, user=cast(User, request.user))

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class DuplicateWellPlannerCompleteStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Duplicate well planner complete step",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        complete_step = get_object_or_404(
            self.well_planner.complete_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_complete_step_id'],
        )

        duplicate_well_planner_complete_step(complete_step=complete_step, user=cast(User, request.user))

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class MoveWellPlannerPlannedStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=MoveWellPlannerStepSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Move well planner planned step",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        planned_step = self.planned_step

        serializer = MoveWellPlannerStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        move_well_planner_planned_step(
            user=cast(User, self.request.user), step=planned_step, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class MoveWellPlannerCompleteStepApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=MoveWellPlannerStepSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Move well planner complete step",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        complete_step = self.complete_step

        serializer = MoveWellPlannerStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        move_well_planner_complete_step(
            user=cast(User, self.request.user), step=complete_step, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class WellReferenceMaterialApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        summary="Well reference material",
        responses={200: WellReferenceMaterialSerializer},
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        object = get_object_or_404(WellReferenceMaterial.objects.filter(tenant=self.tenant))
        return Response(WellReferenceMaterialSerializer(object).data)


class WellPlannerPlannedStepCO2Api(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: WellPlannerPlannedStepCO2Serializer},
        summary="Get well planner planned step CO2",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        step_co2 = get_well_planner_planned_step_co2(planned_step=self.planned_step, user=cast(User, request.user))

        response_data = WellPlannerPlannedStepCO2Serializer(step_co2).data

        return Response(response_data, status=200)


class UpdateWellPlannerPlannedStepEmissionReductionInitiativesApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateWellPlannerEmissionReductionInitiativesSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planner planned step emission reduction initiatives",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        planned_step = get_object_or_404(
            self.well_planner.planned_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_planned_step_id'],
        )
        serializer = UpdateWellPlannerEmissionReductionInitiativesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planner_planned_step_emission_reduction_initiatives(
            planned_step=planned_step, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class UpdateWellPlannerCompleteStepEmissionReductionInitiativesApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateWellPlannerEmissionReductionInitiativesSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planner complete step emission reduction initiatives",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        complete_step = get_object_or_404(
            self.well_planner.complete_steps.all(),  # type: ignore
            pk=self.kwargs['well_planner_complete_step_id'],
        )

        serializer = UpdateWellPlannerEmissionReductionInitiativesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planner_complete_step_emission_reduction_initiatives(
            complete_step=complete_step, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(self.well_planner).data
        return Response(response_data, status=200)


class ApproveWellPlannerCompleteHelicopterUsesApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=ApproveWellPlannerCompleteHelicopterUsesSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Approve well planner complete helicopter uses",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = ApproveWellPlannerCompleteHelicopterUsesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approve_well_planner_complete_helicopter_uses(
            user=cast(User, request.user), well_planner=well_planner, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class ApproveWellPlannerCompleteVesselUsesApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=ApproveWellPlannerCompleteVesselUsesSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Approve well planner complete vessel uses",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = ApproveWellPlannerCompleteVesselUsesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approve_well_planner_complete_vessel_uses(
            user=cast(User, request.user), well_planner=well_planner, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class UpdateWellPlannerActualStartDateApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        request=UpdateWellPlannerActualStartDateSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planner actual start date",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = UpdateWellPlannerActualStartDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planner_actual_start_date(
            user=cast(User, request.user), well_planner=well_planner, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class WellPlannerPhaseListApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: WellPlannerPhaseListSerializer(many=True)}, summary="Well planner phase list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner_phases = (
            CustomPhase.objects.select_related('phase')
            .filter(
                asset=self.well_planner.asset,
                pk__in=BaselineInput.objects.filter(baseline=self.well_planner.baseline)
                .distinct('phase')
                .values_list('phase', flat=True),
            )
            .order_by('name')
        )

        response_data = WellPlannerPhaseListSerializer(well_planner_phases, many=True).data
        return Response(response_data, status=200)


class WellPlannerModeListApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(responses={200: WellPlannerModeListSerializer(many=True)}, summary="Well planner mode list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        custom_well_planner_modes = (
            CustomMode.objects.select_related('mode')
            .filter(
                asset=self.well_planner.asset,
                pk__in=BaselineInput.objects.filter(baseline=self.well_planner.baseline)
                .distinct('mode')
                .values_list('mode', flat=True),
            )
            .order_by('name')
        )

        response_data = WellPlannerModeListSerializer(custom_well_planner_modes, many=True).data
        return Response(response_data, status=200)


class WellPlannerEmissionReductionInitiativeListApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser]

    @extend_schema(
        responses={200: EmissionReductionInitiativeListSerializer(many=True)},
        summary="Emission reduction initiative list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_reduction_initiative = available_emission_reduction_initiatives(self.well_planner)

        response_data = EmissionReductionInitiativeListSerializer(emission_reduction_initiative, many=True).data
        return Response(response_data, status=200)


class WellPlannerListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser]
    serializer_class = WellPlannerListSerializer

    def get_queryset(self) -> QuerySet[WellPlanner]:
        return (
            WellPlanner.objects.live()
            .filter(asset__tenant=self.tenant)
            .select_related('asset', 'baseline', 'name')
            .order_by('-created_at')
        )

    @extend_schema(responses={200: WellPlannerListSerializer(many=True)}, summary="Well planner list")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)
