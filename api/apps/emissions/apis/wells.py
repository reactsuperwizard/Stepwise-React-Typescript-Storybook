from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.emissions.models import BaselineCO2, TargetCO2, TargetCO2Reduction, WellName
from apps.emissions.serializers import (
    CreateUpdateCompleteHelicopterUseSerializer,
    CreateUpdateCompleteVesselUseSerializer,
    CreateUpdatePlannedHelicopterUseSerializer,
    CreateUpdatePlannedVesselUseSerializer,
    CreateUpdateWellSerializer,
    CreateWellNameSerializer,
    UpdateWellPlannedStartDateSerializer,
    WellCO2EmissionSerializer,
    WellNameListSerializer,
)
from apps.emissions.serializers.wells import WellEmissionReductionSerializer
from apps.emissions.services import (
    create_complete_helicopter_use,
    create_complete_vessel_use,
    create_planned_helicopter_use,
    create_planned_vessel_use,
    create_well,
    create_well_name,
    delete_complete_helicopter_use,
    delete_complete_vessel_use,
    delete_planned_helicopter_use,
    delete_planned_vessel_use,
    delete_well,
    duplicate_well,
    get_co2_emissions,
    get_emission_reductions,
    update_complete_helicopter_use,
    update_complete_vessel_use,
    update_planned_helicopter_use,
    update_planned_vessel_use,
    update_well,
    update_well_planned_start_date,
)
from apps.tenants.mixins import TenantMixin
from apps.tenants.models import User
from apps.tenants.permissions import IsAdminUser, IsTenantUser
from apps.wells.mixins import WellPlannerMixin
from apps.wells.serializers import WellPlannerDetailsSerializer, WellPlannerListSerializer


class DeleteWellApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={204: None}, summary="Delete well")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        delete_well(user=cast(User, request.user), well=self.well_planner)
        return Response(status=204)


class DuplicateWellApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={201: WellPlannerListSerializer}, summary="Duplicate well")
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        duplicated_well = duplicate_well(user=cast(User, request.user), well=self.well_planner)

        response_data = WellPlannerListSerializer(duplicated_well).data
        return Response(response_data, status=201)


class CreateWellApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateWellSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateUpdateWellSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        well_planner = create_well(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=201)


class UpdateWellApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateWellSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner

        serializer = CreateUpdateWellSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_well_planner = update_well(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(updated_well_planner).data
        return Response(response_data, status=200)


class WellNameListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellNameListSerializer(many=True)},
        summary="Well name list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_names = WellName.objects.filter(tenant=self.tenant).order_by("name")
        return Response(WellNameListSerializer(well_names, many=True).data)


class CreateWellNameApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateWellNameSerializer,
        responses={200: WellNameListSerializer},
        summary="Create well name",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateWellNameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        well_name = create_well_name(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(WellNameListSerializer(well_name).data, status=201)


class CreateWellPlannedVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdatePlannedVesselUseSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well planned vessel use",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = CreateUpdatePlannedVesselUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_planned_vessel_use(well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=201)


class UpdateWellPlannedVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdatePlannedVesselUseSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planned vessel use",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        planned_vessel_use = get_object_or_404(
            well_planner.plannedvesseluse_set.all(),
            pk=self.kwargs['planned_vessel_use_id'],
        )

        serializer = CreateUpdatePlannedVesselUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_planned_vessel_use(
            planned_vessel_use=planned_vessel_use, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class DeleteWellPlannedVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Delete well planned vessel use",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        planned_vessel_use = get_object_or_404(
            well_planner.plannedvesseluse_set.all(),
            pk=self.kwargs['planned_vessel_use_id'],
        )

        delete_planned_vessel_use(user=cast(User, request.user), planned_vessel_use=planned_vessel_use)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class CreateWellCompleteVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCompleteVesselUseSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well complete vessel use",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = CreateUpdateCompleteVesselUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_complete_vessel_use(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=201)


class UpdateWellCompleteVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCompleteVesselUseSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well complete vessel use",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        complete_vessel_use = get_object_or_404(
            well_planner.completevesseluse_set.all(),
            pk=self.kwargs['complete_vessel_use_id'],
        )

        serializer = CreateUpdateCompleteVesselUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_complete_vessel_use(
            complete_vessel_use=complete_vessel_use, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class DeleteWellCompleteVesselUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Delete well complete vessel use",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        complete_vessel_use = get_object_or_404(
            well_planner.completevesseluse_set.all(),
            pk=self.kwargs['complete_vessel_use_id'],
        )

        delete_complete_vessel_use(user=cast(User, request.user), complete_vessel_use=complete_vessel_use)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class UpdateWellPlannedStartDateApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=UpdateWellPlannedStartDateSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planned start date",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = UpdateWellPlannedStartDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_well_planned_start_date(
            user=cast(User, request.user), well_planner=well_planner, **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class CreateWellPlannedHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdatePlannedHelicopterUseSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well planned helicopter use",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = CreateUpdatePlannedHelicopterUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_planned_helicopter_use(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=201)


class UpdateWellPlannedHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdatePlannedHelicopterUseSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well planned helicopter use",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        planned_helicopter_use = get_object_or_404(
            well_planner.plannedhelicopteruse_set.all(),
            pk=self.kwargs['planned_helicopter_use_id'],
        )

        serializer = CreateUpdatePlannedHelicopterUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_planned_helicopter_use(
            planned_helicopter_use=planned_helicopter_use, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class DeleteWellPlannedHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Delete well planned helicopter use",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        planned_helicopter_use = get_object_or_404(
            well_planner.plannedhelicopteruse_set.all(),
            pk=self.kwargs['planned_helicopter_use_id'],
        )

        delete_planned_helicopter_use(user=cast(User, request.user), planned_helicopter_use=planned_helicopter_use)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class CreateWellCompleteHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCompleteHelicopterUseSerializer,
        responses={201: WellPlannerDetailsSerializer},
        summary="Create well complete helicopter use",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        serializer = CreateUpdateCompleteHelicopterUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        create_complete_helicopter_use(
            well_planner=well_planner, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=201)


class UpdateWellCompleteHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCompleteHelicopterUseSerializer,
        responses={200: WellPlannerDetailsSerializer},
        summary="Update well complete helicopter use",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        complete_helicopter_use = get_object_or_404(
            well_planner.completehelicopteruse_set.all(),
            pk=self.kwargs['complete_helicopter_use_id'],
        )

        serializer = CreateUpdateCompleteHelicopterUseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_complete_helicopter_use(
            complete_helicopter_use=complete_helicopter_use, user=cast(User, request.user), **serializer.validated_data
        )

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class DeleteWellCompleteHelicopterUseApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellPlannerDetailsSerializer},
        summary="Delete well complete helicopter use",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        well_planner = self.well_planner
        complete_helicopter_use = get_object_or_404(
            well_planner.completehelicopteruse_set.all(),
            pk=self.kwargs['complete_helicopter_use_id'],
        )

        delete_complete_helicopter_use(user=cast(User, request.user), complete_helicopter_use=complete_helicopter_use)

        response_data = WellPlannerDetailsSerializer(well_planner).data
        return Response(response_data, status=200)


class WellTargetCO2EmissionsApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellCO2EmissionSerializer(many=True)},
        summary="Well target CO2 emissions",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        dataset = get_co2_emissions(well_planner=self.well_planner, co2_model=TargetCO2)
        response_data = WellCO2EmissionSerializer(dataset, many=True).data

        return Response(response_data, status=200)


class WellBaselineCO2EmissionsApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellCO2EmissionSerializer(many=True)},
        summary="Well baseline CO2 emissions",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        dataset = get_co2_emissions(well_planner=self.well_planner, co2_model=BaselineCO2)
        response_data = WellCO2EmissionSerializer(dataset, many=True).data

        return Response(response_data, status=200)


class WellTargetCO2EmissionReductionsApi(WellPlannerMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: WellEmissionReductionSerializer(many=True)},
        summary="Well target CO2 emission reductions",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        dataset = get_emission_reductions(well_plan=self.well_planner, reduction_model=TargetCO2Reduction)
        response_data = WellEmissionReductionSerializer(dataset, many=True).data

        return Response(response_data, status=200)
