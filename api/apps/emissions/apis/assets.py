from typing import cast

from django.contrib.auth.models import User
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.emissions.models import Asset, AssetReferenceMaterial, HelicopterType, VesselType
from apps.emissions.models.assets import MaterialType
from apps.emissions.serializers import (
    AllHelicopterTypeListSerializer,
    AllMaterialTypeListSerializer,
    AllVesselTypeListSerializer,
    AssetDetailsSerializer,
    AssetListSerializer,
    AssetModeSerializer,
    AssetPhaseSerializer,
    AssetReferenceMaterialSerializer,
    BaselineDetailsSerializer,
    BaselineModeSerializer,
    BaselinePhaseSerializer,
    CompleteAssetListSerializer,
    CreateAssetSerializer,
    CreateMaterialTypeSerializer,
    CreateUpdateBaselineSerializer,
    CreateUpdateCustomModeSerializer,
    CreateUpdateCustomPhaseSerializer,
    CreateUpdateEmissionManagementPlanSerializer,
    CreateUpdateEmissionReductionInitiativeSerializer,
    CreateUpdateHelicopterTypeSerializer,
    CreateUpdateVesselTypeSerializer,
    EmissionManagementPlanDetailsSerializer,
    EmissionReductionInitiativeDetailsSerializer,
    HelicopterTypeListSerializer,
    MaterialTypeListSerializer,
    UpdateAssetSerializer,
    UpdateMaterialTypeSerializer,
    VesselTypeListSerializer,
)
from apps.emissions.services import (
    activate_baseline,
    activate_emission_management_plan,
    create_asset,
    create_baseline,
    create_custom_mode,
    create_custom_phase,
    create_emission_management_plan,
    create_emission_reduction_initiative,
    create_helicopter_type,
    create_material_type,
    create_vessel_type,
    delete_asset,
    delete_baseline,
    delete_emission_management_plan,
    delete_emission_reduction_initiative,
    delete_helicopter_type,
    delete_material_type,
    duplicate_asset,
    duplicate_baseline,
    duplicate_emission_management_plan,
    update_asset,
    update_baseline,
    update_custom_mode,
    update_custom_phase,
    update_emission_management_plan,
    update_emission_reduction_initiative,
    update_helicopter_type,
    update_material_type,
    update_vessel_type,
)
from apps.emissions.services.assets import baseline_modes, baseline_phases, delete_vessel_type, get_complete_assets
from apps.emissions.utils.mixins import AssetMixin, BaselineMixin, EmissionManagementPlanMixin
from apps.tenants.mixins import TenantMixin
from apps.tenants.permissions import IsAdminUser, IsTenantUser


class AssetListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser, IsAdminUser]
    serializer_class = AssetListSerializer

    def get_queryset(self) -> QuerySet['Asset']:
        return Asset.objects.live().filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Asset list", description="Returns a list of both draft and non-draft assets")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class CompleteAssetListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: CompleteAssetListSerializer(many=True)},
        summary="Complete asset list",
        description="Returns a list of non-draft assets",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        assets = get_complete_assets(self.tenant)

        response_data = CompleteAssetListSerializer(assets, many=True).data
        return Response(response_data, status=200)


class CreateAssetApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateAssetSerializer,
        responses={201: AssetDetailsSerializer},
        summary="Create asset",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_asset = create_asset(tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data)
        return Response(AssetDetailsSerializer(created_asset).data, status=201)


class UpdateAssetApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=UpdateAssetSerializer,
        responses={200: AssetDetailsSerializer},
        summary="Update asset",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = UpdateAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_asset = update_asset(asset=self.asset, user=cast(User, request.user), **serializer.validated_data)
        return Response(AssetDetailsSerializer(updated_asset).data, status=200)


class AssetDetailsApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetDetailsSerializer},
        summary="Asset details",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return Response(AssetDetailsSerializer(self.asset).data, status=200)


class DuplicateAssetApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={201: AssetListSerializer},
        summary="Duplicate asset",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        asset_copy = duplicate_asset(asset=self.asset, user=cast(User, request.user))
        return Response(AssetListSerializer(asset_copy).data, status=201)


class DeleteAssetApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={204: None},
        summary="Delete asset",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        delete_asset(asset=self.asset, user=cast(User, request.user))
        return Response(status=204)


class AssetReferenceMaterialApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        summary="Asset reference material",
        responses={200: AssetReferenceMaterialSerializer},
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        reference_material = get_object_or_404(AssetReferenceMaterial.objects.filter(tenant=self.tenant))
        return Response(AssetReferenceMaterialSerializer(reference_material).data)


class ActivateBaselineApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetDetailsSerializer.BaselineSerializer},
        summary="Activate asset",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        activated_baseline = activate_baseline(baseline=self.baseline, user=cast(User, request.user))
        return Response(AssetDetailsSerializer.BaselineSerializer(activated_baseline).data, status=200)


class DeleteBaselineApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetDetailsSerializer},
        summary="Delete baseline",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        delete_baseline(baseline=self.baseline, user=cast(User, request.user))
        return Response(AssetDetailsSerializer(self.asset).data, status=200)


class DuplicateBaselineApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={201: AssetDetailsSerializer.BaselineSerializer},
        summary="Duplicate baseline",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        duplicated_baseline = duplicate_baseline(baseline=self.baseline, user=cast(User, request.user))
        return Response(AssetDetailsSerializer.BaselineSerializer(duplicated_baseline).data, status=201)


class AssetPhaseListApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetPhaseSerializer(many=True)},
        summary="Asset phase list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        phases = self.asset.customphase_set.exclude(phase__transit=True).order_by('id')
        return Response(AssetPhaseSerializer(phases, many=True).data)


class AssetModeListApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetModeSerializer(many=True)},
        summary="Asset mode list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        modes = self.asset.custommode_set.exclude(mode__transit=True).order_by('id')
        return Response(AssetModeSerializer(modes, many=True).data)


class CreateAssetCustomPhaseApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCustomPhaseSerializer,
        responses={201: AssetPhaseSerializer},
        summary="Create asset custom phase",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        asset = self.asset
        serializer = CreateUpdateCustomPhaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        custom_phase = create_custom_phase(user=cast(User, request.user), asset=asset, **serializer.validated_data)

        response_data = AssetPhaseSerializer(custom_phase).data
        return Response(response_data, status=201)


class UpdateAssetCustomPhaseApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCustomPhaseSerializer,
        responses={200: AssetPhaseSerializer},
        summary="Update asset custom phase",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        custom_phase = get_object_or_404(
            self.asset.customphase_set.all(),
            pk=kwargs["custom_phase_id"],
        )

        serializer = CreateUpdateCustomPhaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_custom_phase = update_custom_phase(
            user=cast(User, request.user),
            custom_phase=custom_phase,
            **serializer.validated_data,
        )

        response_data = AssetPhaseSerializer(updated_custom_phase).data
        return Response(response_data, status=200)


class CreateAssetCustomModeApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCustomModeSerializer,
        responses={201: AssetModeSerializer},
        summary="Create asset custom mode",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        asset = self.asset
        serializer = CreateUpdateCustomModeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        custom_mode = create_custom_mode(user=cast(User, request.user), asset=asset, **serializer.validated_data)

        response_data = AssetModeSerializer(custom_mode).data
        return Response(response_data, status=201)


class UpdateAssetCustomModeApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateCustomModeSerializer,
        responses={200: AssetModeSerializer},
        summary="Update asset custom mode",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        custom_mode = get_object_or_404(
            self.asset.custommode_set.all(),
            pk=kwargs["custom_mode_id"],
        )

        serializer = CreateUpdateCustomModeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_custom_mode = update_custom_mode(
            user=cast(User, request.user),
            custom_mode=custom_mode,
            **serializer.validated_data,
        )

        response_data = AssetModeSerializer(updated_custom_mode).data
        return Response(response_data, status=200)


class AssetBaselineDetailsApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: BaselineDetailsSerializer},
        summary="Baseline details",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return Response(BaselineDetailsSerializer(self.baseline).data)


class CreateAssetBaselineApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateBaselineSerializer,
        responses={201: BaselineDetailsSerializer},
        summary="Create baseline",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        asset = self.asset
        serializer = CreateUpdateBaselineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        baseline = create_baseline(user=cast(User, request.user), asset=asset, **serializer.validated_data)

        response_data = BaselineDetailsSerializer(baseline).data
        return Response(response_data, status=201)


class UpdateAssetBaselineApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateBaselineSerializer,
        responses={200: BaselineDetailsSerializer},
        summary="Update baseline",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        baseline = self.baseline

        serializer = CreateUpdateBaselineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_baseline = update_baseline(
            user=cast(User, request.user), baseline=baseline, **serializer.validated_data
        )

        response_data = BaselineDetailsSerializer(updated_baseline).data
        return Response(response_data, status=200)


class VesselTypeListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser, IsAdminUser]
    serializer_class = VesselTypeListSerializer

    def get_queryset(self) -> QuerySet[VesselType]:
        return VesselType.objects.live().filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Paginated list of vessel types")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class AllVesselTypeListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={200: AllVesselTypeListSerializer(many=True)}, summary="List of all vessel types")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        vessel_types = VesselType.objects.live().filter(tenant=self.tenant).order_by('created_at')

        response_data = AllVesselTypeListSerializer(vessel_types, many=True).data
        return Response(response_data, status=200)


class EmissionReductionInitiativeDetailsApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: EmissionReductionInitiativeDetailsSerializer},
        summary="Emission reduction initiative details",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_reduction_initiative = get_object_or_404(
            self.emission_management_plan.emission_reduction_initiatives.live(),
            pk=kwargs["emission_reduction_initiative_id"],
        )

        response_data = EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative).data
        return Response(response_data)


class CreateEmissionReductionInitiativeApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateEmissionReductionInitiativeSerializer,
        responses={201: EmissionReductionInitiativeDetailsSerializer},
        summary="Create emission reduction initiative",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_management_plan = self.emission_management_plan
        serializer = CreateUpdateEmissionReductionInitiativeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emission_reduction_initiative = create_emission_reduction_initiative(
            user=cast(User, request.user),
            emission_management_plan=emission_management_plan,
            **serializer.validated_data,
        )

        response_data = EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative).data
        return Response(response_data, status=201)


class UpdateEmissionReductionInitiativeApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateEmissionReductionInitiativeSerializer,
        responses={200: EmissionReductionInitiativeDetailsSerializer},
        summary="Update emission reduction initiative",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_reduction_initiative = get_object_or_404(
            self.emission_management_plan.emission_reduction_initiatives.live(),
            pk=kwargs["emission_reduction_initiative_id"],
        )

        serializer = CreateUpdateEmissionReductionInitiativeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_emission_reduction_initiative = update_emission_reduction_initiative(
            user=cast(User, request.user),
            emission_reduction_initiative=emission_reduction_initiative,
            **serializer.validated_data,
        )
        response_data = EmissionReductionInitiativeDetailsSerializer(updated_emission_reduction_initiative).data
        return Response(response_data, status=200)


class CreateVesselTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateVesselTypeSerializer,
        responses={201: VesselTypeListSerializer},
        summary="Create vessel type",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateUpdateVesselTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_vessel_type = create_vessel_type(
            tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(VesselTypeListSerializer(created_vessel_type).data, status=201)


class UpdateVesselTypeApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateVesselTypeSerializer,
        responses={200: VesselTypeListSerializer},
        summary="Update vessel type",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        vessel_type = get_object_or_404(
            VesselType.objects.live().filter(tenant=self.tenant), pk=kwargs['vessel_type_id']
        )
        serializer = CreateUpdateVesselTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_vessel_type = update_vessel_type(
            vessel_type=vessel_type, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(VesselTypeListSerializer(updated_vessel_type).data, status=200)


class DeleteVesselTypeApi(AssetMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={204: None},
        summary="Delete vessel type",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        vessel_type = get_object_or_404(
            VesselType.objects.live().filter(tenant=self.tenant), pk=kwargs['vessel_type_id']
        )

        delete_vessel_type(vessel_type=vessel_type, user=cast(User, request.user))
        return Response(status=204)


class EmissionManagementPlanDetailsApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={200: EmissionManagementPlanDetailsSerializer}, summary="Emission management plan details")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        response_data = EmissionManagementPlanDetailsSerializer(self.emission_management_plan).data
        return Response(response_data, status=200)


class CreateEmissionManagementPlanApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateEmissionManagementPlanSerializer,
        responses={201: EmissionManagementPlanDetailsSerializer},
        summary="Create emission management plan",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        baseline = self.baseline

        serializer = CreateUpdateEmissionManagementPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emission_management_plan = create_emission_management_plan(
            user=cast(User, request.user),
            baseline=baseline,
            **serializer.validated_data,
        )

        response_data = EmissionManagementPlanDetailsSerializer(emission_management_plan).data
        return Response(response_data, status=201)


class UpdateEmissionManagementPlanApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateEmissionManagementPlanSerializer,
        responses={200: EmissionManagementPlanDetailsSerializer},
        summary="Update emission management plan",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_management_plan = self.emission_management_plan

        serializer = CreateUpdateEmissionManagementPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_emission_management_plan = update_emission_management_plan(
            user=cast(User, request.user),
            emission_management_plan=emission_management_plan,
            **serializer.validated_data,
        )

        response_data = EmissionManagementPlanDetailsSerializer(updated_emission_management_plan).data
        return Response(response_data, status=200)


class DeleteEmissionManagementPlanApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={204: None}, summary="Delete emission management plan")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        delete_emission_management_plan(
            user=cast(User, request.user),
            emission_management_plan=self.emission_management_plan,
        )
        return Response(status=204)


class ActivateEmissionManagementPlanApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AssetDetailsSerializer.EmissionManagementPlanSerializer},
        summary="Activate emission management plan",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        activated_emission_management_plan = activate_emission_management_plan(
            user=cast(User, request.user), emission_management_plan=self.emission_management_plan
        )
        response_data = AssetDetailsSerializer.EmissionManagementPlanSerializer(activated_emission_management_plan).data
        return Response(response_data, status=200)


class DuplicateEmissionManagementPlanApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={201: AssetDetailsSerializer.EmissionManagementPlanSerializer},
        summary="Duplicate emission management plan",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_management_plan = self.emission_management_plan

        duplicated_emission_management_plan = duplicate_emission_management_plan(
            user=cast(User, request.user),
            emission_management_plan=emission_management_plan,
        )

        response_data = AssetDetailsSerializer.EmissionManagementPlanSerializer(
            duplicated_emission_management_plan
        ).data
        return Response(response_data, status=201)


class DeleteEmissionReductionInitiativeApi(EmissionManagementPlanMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={204: None}, summary="Delete emission reduction initiative")
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        emission_reduction_initiative = get_object_or_404(
            self.emission_management_plan.emission_reduction_initiatives.live(),
            pk=kwargs['emission_reduction_initiative_id'],
        )

        delete_emission_reduction_initiative(
            user=cast(User, request.user),
            emission_reduction_initiative=emission_reduction_initiative,
        )
        return Response(status=204)


class HelicopterTypeListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser, IsAdminUser]
    serializer_class = HelicopterTypeListSerializer

    def get_queryset(self) -> QuerySet[HelicopterType]:
        return HelicopterType.objects.live().filter(tenant=self.tenant).order_by('-created_at')

    @extend_schema(summary="Paginated list of helicopter types")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class AllHelicopterTypeListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(responses={200: AllHelicopterTypeListSerializer(many=True)}, summary="List of all helicopter types")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        helicopter_types = HelicopterType.objects.live().filter(tenant=self.tenant).order_by('created_at')

        response_data = AllHelicopterTypeListSerializer(helicopter_types, many=True).data
        return Response(response_data, status=200)


class MaterialTypeListApi(TenantMixin, ListAPIView):
    permission_classes = [IsTenantUser, IsAdminUser]
    serializer_class = MaterialTypeListSerializer

    def get_queryset(self) -> QuerySet[MaterialType]:
        return cast(
            QuerySet[MaterialType], MaterialType.objects.live().filter(tenant=self.tenant).order_by('-created_at')
        )

    @extend_schema(summary="Paginated list of material types")
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        return super().get(request, *args, **kwargs)


class DeleteHelicopterTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={204: None},
        summary="Delete helicopter type",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        helicopter_type = get_object_or_404(
            HelicopterType.objects.live().filter(tenant=self.tenant), pk=kwargs['helicopter_type_id']
        )

        delete_helicopter_type(helicopter_type=helicopter_type, user=cast(User, request.user))

        return Response(status=204)


class CreateHelicopterTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateHelicopterTypeSerializer,
        responses={201: HelicopterTypeListSerializer},
        summary="Create helicopter type",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateUpdateHelicopterTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_helicopter_type = create_helicopter_type(
            tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(HelicopterTypeListSerializer(created_helicopter_type).data, status=201)


class UpdateHelicopterTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateUpdateHelicopterTypeSerializer,
        responses={200: HelicopterTypeListSerializer},
        summary="Update helicopter type",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        helicopter_type = get_object_or_404(self.tenant.helicoptertype_set.all(), pk=kwargs['helicopter_type_id'])
        serializer = CreateUpdateHelicopterTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_helicopter_type = update_helicopter_type(
            helicopter_type=helicopter_type, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(HelicopterTypeListSerializer(updated_helicopter_type).data, status=200)


class BaselinePhaseListApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: BaselinePhaseSerializer(many=True)},
        summary="Baseline phase list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        phases = baseline_phases(self.baseline).exclude(phase__transit=True)
        return Response(BaselinePhaseSerializer(phases, many=True).data)


class BaselineModeListApi(BaselineMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: BaselineModeSerializer(many=True)},
        summary="Baseline mode list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        modes = baseline_modes(self.baseline).exclude(mode__transit=True)
        return Response(BaselineModeSerializer(modes, many=True).data)


class DeleteMaterialTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={204: None},
        summary="Delete material type",
    )
    def delete(self, request: Request, *args: str, **kwargs: str) -> Response:
        material_type = get_object_or_404(
            MaterialType.objects.live().filter(tenant=self.tenant), pk=kwargs['material_type_id']
        )

        delete_material_type(material_type=material_type, user=cast(User, request.user))

        return Response(status=204)


class CreateMaterialTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=CreateMaterialTypeSerializer,
        responses={201: MaterialTypeListSerializer},
        summary="Create material type",
    )
    def post(self, request: Request, *args: str, **kwargs: str) -> Response:
        serializer = CreateMaterialTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_material_type = create_material_type(
            tenant=self.tenant, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(MaterialTypeListSerializer(created_material_type).data, status=201)


class UpdateMaterialTypeApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        request=UpdateMaterialTypeSerializer,
        responses={200: MaterialTypeListSerializer},
        summary="Update material type",
    )
    def put(self, request: Request, *args: str, **kwargs: str) -> Response:
        material_type = get_object_or_404(
            MaterialType.objects.live().filter(tenant=self.tenant), pk=kwargs['material_type_id']
        )

        serializer = UpdateMaterialTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_material_type = update_material_type(
            material_type=material_type, user=cast(User, request.user), **serializer.validated_data
        )
        return Response(MaterialTypeListSerializer(updated_material_type).data, status=200)


class AllMaterialTypeListApi(TenantMixin, APIView):
    permission_classes = [IsTenantUser, IsAdminUser]

    @extend_schema(
        responses={200: AllMaterialTypeListSerializer(many=True)},
        summary="All material type list",
    )
    def get(self, request: Request, *args: str, **kwargs: str) -> Response:
        material_types = MaterialType.objects.live().filter(tenant=self.tenant).order_by('created_at')

        response_data = AllMaterialTypeListSerializer(material_types, many=True).data
        return Response(response_data, status=200)
