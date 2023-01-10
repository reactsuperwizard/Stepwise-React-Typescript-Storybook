import datetime

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.emissions.factories import (
    AssetFactory,
    AssetReferenceMaterialFactory,
    BaselineFactory,
    BaselineInputFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionManagementPlanFactory,
    EmissionReductionInitiativeFactory,
    EmissionReductionInitiativeInputFactory,
    ExternalEnergySupplyFactory,
    HelicopterTypeFactory,
    MaterialTypeFactory,
    VesselTypeFactory,
)
from apps.emissions.models import (
    Asset,
    AssetSeason,
    AssetType,
    Baseline,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    EmissionReductionInitiativeType,
    HelicopterType,
    MaterialCategory,
    MaterialType,
    VesselType,
)
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
    EmissionManagementPlanDetailsSerializer,
    EmissionReductionInitiativeDetailsSerializer,
    HelicopterTypeListSerializer,
    MaterialTypeListSerializer,
    VesselTypeListSerializer,
)
from apps.emissions.services.assets import get_complete_assets
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory
from apps.tenants.models import UserRole


@pytest.mark.django_db
class TestAssetListApi:
    def test_should_retrieve_asset_list(self):
        tenant_user = TenantUserRelationFactory()
        draft_asset = AssetFactory(tenant=tenant_user.tenant, draft=True)
        complete_asset = AssetFactory(tenant=tenant_user.tenant, draft=False)
        AssetFactory(tenant=tenant_user.tenant, deleted=True)
        AssetFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:asset_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': AssetListSerializer([complete_asset, draft_asset], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:asset_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:asset_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCompleteAssetListApi:
    def test_should_retrieve_complete_asset_list(self):
        tenant_user = TenantUserRelationFactory()
        complete_asset = AssetFactory(tenant=tenant_user.tenant, draft=False)
        AssetFactory(tenant=tenant_user.tenant, draft=False, deleted=True)
        AssetFactory(tenant=tenant_user.tenant, draft=True)
        AssetFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:complete_asset_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        complete_asset = get_complete_assets(tenant_user.tenant).get(pk=complete_asset.pk)
        assert response.data == CompleteAssetListSerializer([complete_asset], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:complete_asset_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:complete_asset_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateAssetApi:
    @pytest.fixture
    def data(self):
        return {
            "name": "Asset",
            "type": AssetType.SEMI,
            "draft": False,
            "design_description": "Design description",
            "green_house_gas_class_notation": "Green house gas",
            "external_energy_supply": {
                "type": "External energy supply",
                "capacity": 1,
                "co2": 2,
                "nox": 3,
                "generator_efficiency_factor": 4,
            },
        }

    def test_should_create_asset(self, data: dict):
        tenant_user = TenantUserRelationFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:create_asset',
            kwargs={"tenant_id": tenant_user.tenant_id},
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        asset = Asset.objects.get()
        assert response.data == AssetDetailsSerializer(asset).data

    def test_should_be_forbidden_for_anonymous_user(self, data: dict):
        tenant = TenantFactory()
        api_client = APIClient()

        url = reverse(
            'emissions:create_asset',
            kwargs={"tenant_id": tenant.pk},
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:create_asset',
            kwargs={"tenant_id": tenant.pk},
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateAssetApi:
    @pytest.fixture
    def data(self):
        return {
            "name": "Asset",
            "type": AssetType.SEMI,
            "design_description": "Design description",
            "draft": False,
            "green_house_gas_class_notation": "Green house gas",
            "external_energy_supply": {
                "type": "External energy supply",
                "capacity": 1,
                "co2": 2,
                "nox": 3,
                "generator_efficiency_factor": 4,
            },
        }

    def test_should_update_asset(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, draft=True)
        BaselineFactory(asset=asset, active=True, draft=False)
        ExternalEnergySupplyFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        asset.refresh_from_db()
        assert response.data == AssetDetailsSerializer(asset).data

    def test_should_be_not_found_for_deleted_asset(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, draft=True, deleted=True)
        ExternalEnergySupplyFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_asset(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        asset = AssetFactory()
        ExternalEnergySupplyFactory(asset=asset)

        url = reverse(
            'emissions:update_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self, data: dict):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        ExternalEnergySupplyFactory(asset=asset)
        api_client = APIClient()

        url = reverse(
            'emissions:update_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        ExternalEnergySupplyFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAssetDetailsApi:
    def test_should_get_asset_details(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_details',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AssetDetailsSerializer(asset).data

    def test_should_be_not_found_for_deleted_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_details',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_details',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'emissions:asset_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:asset_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDuplicateAssetApi:
    def test_should_duplicate_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        ExternalEnergySupplyFactory(asset=asset)
        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(baseline=baseline, phase__asset=asset, mode__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        assert Asset.objects.count() == 1

        url = reverse(
            'emissions:duplicate_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 201
        asset_copy = Asset.objects.order_by('id').last()
        assert response.data == AssetListSerializer(asset_copy).data
        assert Asset.objects.count() == 2

    def test_should_be_not_found_for_deleted_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, deleted=True)
        ExternalEnergySupplyFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:duplicate_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        asset = AssetFactory()
        ExternalEnergySupplyFactory(asset=asset)

        url = reverse(
            'emissions:duplicate_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        ExternalEnergySupplyFactory(asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:duplicate_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        ExternalEnergySupplyFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:duplicate_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteAssetApi:
    def test_should_delete_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_deleted_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        asset = AssetFactory()

        url = reverse(
            'emissions:delete_asset',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'emissions:delete_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:delete_asset',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAssetReferenceMaterialApi:
    def test_should_retrieve_asset_reference_material(self):
        tenant_user = TenantUserRelationFactory()
        reference_material = AssetReferenceMaterialFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_reference_material',
            kwargs={"tenant_id": tenant_user.tenant.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AssetReferenceMaterialSerializer(reference_material).data

    def test_should_be_not_found_for_non_existing_material(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:asset_reference_material', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        AssetReferenceMaterialFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('emissions:asset_reference_material', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        AssetReferenceMaterialFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:asset_reference_material', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestActivateBaselineApi:
    def test_should_activate_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset, draft=False, active=False)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:activate_baseline',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 200
        baseline.refresh_from_db()
        assert response.data == AssetDetailsSerializer.BaselineSerializer(baseline).data

    def test_should_be_not_found_for_unknown_baseline(self):
        tenant_user = TenantUserRelationFactory()
        baseline = BaselineFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:activate_baseline',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": baseline.asset_id, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset, draft=False, active=False, deleted=True)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:activate_baseline',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()

        url = reverse(
            'emissions:activate_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:activate_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteBaselineApi:
    def test_should_delete_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_baseline',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 200
        assert response.data == AssetDetailsSerializer(asset).data

    def test_should_be_not_found_for_deleted_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_baseline',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory()
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_baseline',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:delete_baseline',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:delete_baseline',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDuplicateBaselineApi:
    def test_should_duplicate_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(baseline=baseline, phase__asset=asset, mode__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        assert asset.baselines.count() == 1

        url = reverse(
            'emissions:duplicate_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.post(url)

        baseline = asset.baselines.order_by('id').last()
        assert response.status_code == 201
        assert response.data == AssetDetailsSerializer.BaselineSerializer(baseline).data

    def test_should_be_not_found_for_deleted_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:duplicate_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_baseline(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        asset = AssetFactory()
        baseline = BaselineFactory(asset=asset)

        url = reverse(
            'emissions:duplicate_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()

        url = reverse(
            'emissions:duplicate_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:duplicate_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAssetPhaseListApi:
    def test_should_retrieve_asset_phase_list(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        first_phase = CustomPhaseFactory(asset=asset, phase__transit=False)
        second_phase = CustomPhaseFactory(asset=asset, phase=None)
        third_phase = CustomPhaseFactory(asset=asset)
        CustomPhaseFactory(asset=asset, phase__transit=True)
        CustomPhaseFactory(phase=None)
        CustomPhaseFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:asset_phase_list', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AssetPhaseSerializer([first_phase, second_phase, third_phase], many=True).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:asset_phase_list', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('emissions:asset_phase_list', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:asset_phase_list', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAssetModeListApi:
    def test_should_retrieve_asset_mode_list(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        first_mode = CustomModeFactory(asset=asset, mode__transit=False)
        second_mode = CustomModeFactory(asset=asset)
        third_mode = CustomModeFactory(asset=asset, mode=None)
        CustomModeFactory(asset=asset, mode__transit=True)
        CustomModeFactory(mode=None)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:asset_mode_list', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AssetModeSerializer([first_mode, second_mode, third_mode], many=True).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:asset_mode_list', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('emissions:asset_mode_list', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:asset_mode_list', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateAssetCustomPhaseApi:
    def test_should_create_asset_custom_phase(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "name": "Test phase",
            "description": "Test description",
        }

        url = reverse(
            'emissions:create_asset_custom_phase', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk}
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        custom_phase = CustomPhase.objects.get(asset=asset)
        assert response.data == AssetPhaseSerializer(custom_phase).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:create_asset_custom_phase', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0})
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('emissions:create_asset_custom_phase', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:create_asset_custom_phase', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateAssetCustomPhaseApi:
    def test_should_update_asset_custom_phase(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        custom_phase = CustomPhaseFactory(asset=asset, phase=None)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "name": "Test phase",
            "description": "Test description",
        }

        url = reverse(
            'emissions:update_asset_custom_phase',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "custom_phase_id": custom_phase.pk},
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        custom_phase.refresh_from_db()
        assert response.data == AssetPhaseSerializer(custom_phase).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        custom_phase = CustomPhaseFactory(phase=None)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_custom_phase',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0, "custom_phase_id": custom_phase.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_phase(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_custom_phase',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "custom_phase_id": 0},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        custom_phase = CustomPhaseFactory(asset=asset, phase=None)
        api_client = APIClient()

        url = reverse(
            'emissions:update_asset_custom_phase',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "custom_phase_id": custom_phase.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        custom_phase = CustomPhaseFactory(asset=asset, phase=None)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_asset_custom_phase',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "custom_phase_id": custom_phase.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateAssetCustomMode:
    def test_should_create_asset_custom_mode(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "name": "Test mode",
            "description": "Test description",
        }

        url = reverse(
            'emissions:create_asset_custom_mode', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk}
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        assert response.data == AssetModeSerializer(CustomMode.objects.get()).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:create_asset_custom_mode', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0})
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('emissions:create_asset_custom_mode', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:create_asset_custom_mode', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateAssetCustomMode:
    def test_should_update_asset_custom_mode(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        custom_mode = CustomModeFactory(asset=asset, mode=None)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "name": "Test mode",
            "description": "Test description",
        }

        url = reverse(
            'emissions:update_asset_custom_mode',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "custom_mode_id": custom_mode.pk},
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        custom_mode.refresh_from_db()
        assert response.data == AssetModeSerializer(custom_mode).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        custom_mode = CustomModeFactory(mode=None)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_custom_mode',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0, "custom_mode_id": custom_mode.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_mode(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_custom_mode',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "custom_mode_id": 0},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        custom_mode = CustomModeFactory(asset=asset, mode=None)

        api_client = APIClient()

        url = reverse(
            'emissions:update_asset_custom_mode',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "custom_mode_id": custom_mode.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        custom_mode = CustomModeFactory(asset=asset, mode=None)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_asset_custom_mode',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "custom_mode_id": custom_mode.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAssetBaselineDetailsApi:
    def test_should_retrieve_asset_baseline_details(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.WINTER)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_baseline_details',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == BaselineDetailsSerializer(baseline).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        baseline = BaselineFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_baseline_details',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:asset_baseline_details',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": 0},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:asset_baseline_details',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}


@pytest.mark.django_db
class TestVesselTypeListApi:
    def test_should_retrieve_vessel_type_list(self):
        tenant_user = TenantUserRelationFactory()
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)
        VesselTypeFactory(tenant=tenant_user.tenant, deleted=True)
        VesselTypeFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:vessel_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': VesselTypeListSerializer([vessel_type], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:vessel_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:vessel_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateVesselTypeApi:
    @pytest.fixture
    def data(self):
        return {
            "type": "Anchor handling tug supply vessel (AHTS)",
            "fuel_type": "Fuel type",
            "fuel_density": 1.0,
            "co2_per_fuel": 2.0,
            "nox_per_fuel": 3.0,
            "co2_tax": 4.0,
            "nox_tax": 5.0,
            "fuel_cost": 6.0,
            "fuel_consumption_summer": 4.9,
            "fuel_consumption_winter": 5.5,
        }

    def test_should_create_vessel_type(self, data: dict):
        tenant_user = TenantUserRelationFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:create_vessel_type',
            kwargs={"tenant_id": tenant_user.tenant_id},
        )
        response = api_client.post(url, data=data)

        assert response.status_code == 201
        vessel_type = VesselType.objects.get()
        assert response.data == VesselTypeListSerializer(vessel_type).data

    def test_should_be_forbidden_for_anonymous_user(self, data: dict):
        tenant = TenantFactory()
        api_client = APIClient()

        url = reverse(
            'emissions:create_vessel_type',
            kwargs={"tenant_id": tenant.pk},
        )
        response = api_client.post(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:create_vessel_type',
            kwargs={"tenant_id": tenant.pk},
        )
        response = api_client.post(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateVesselTypeApi:
    @pytest.fixture
    def data(self):
        return {
            "type": "Anchor handling tug supply vessel (AHTS)",
            "fuel_type": "Fuel type",
            "fuel_density": 1.0,
            "co2_per_fuel": 2.0,
            "nox_per_fuel": 3.0,
            "co2_tax": 4.0,
            "nox_tax": 5.0,
            "fuel_cost": 6.0,
            "fuel_consumption_summer": 4.9,
            "fuel_consumption_winter": 5.5,
        }

    def test_should_update_vessel_type(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 200
        vessel_type.refresh_from_db()
        assert response.data == VesselTypeListSerializer(vessel_type).data

    def test_should_be_not_found_for_deleted_vessel_type(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant, deleted=True)

        url = reverse(
            'emissions:update_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_vessel_type(self, data: dict):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_type = VesselTypeFactory()

        url = reverse(
            'emissions:update_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self, data: dict):
        tenant = TenantFactory()
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'emissions:update_vessel_type',
            kwargs={
                "tenant_id": tenant.pk,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_vessel_type',
            kwargs={
                "tenant_id": tenant.pk,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteVesselTypeApi:
    def test_should_delete_vessel_type(self):
        tenant_user = TenantUserRelationFactory()
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_deleted_vessel_type(self):
        tenant_user = TenantUserRelationFactory()
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:delete_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_unknown_vessel_type(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_type = VesselTypeFactory()

        url = reverse(
            'emissions:delete_vessel_type',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'emissions:delete_vessel_type',
            kwargs={
                "tenant_id": tenant.pk,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:delete_vessel_type',
            kwargs={
                "tenant_id": tenant.pk,
                "vessel_type_id": vessel_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateAssetBaselineApi:
    def test_should_create_asset_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        CustomPhaseFactory(asset=asset, phase__transit=True)
        CustomModeFactory(asset=asset, mode__transit=True)
        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)

        data = {
            "name": "Test baseline",
            "description": "Test description",
            "boilers_fuel_consumption_summer": 13,
            "boilers_fuel_consumption_winter": 7.5,
            "draft": True,
            "summer": {
                "transit": 0,
                "inputs": [
                    {
                        "phase": phase.pk,
                        "mode": mode.pk,
                        "value": 1,
                    }
                ],
            },
            "winter": {
                "transit": 0,
                "inputs": [
                    {
                        "phase": phase.pk,
                        "mode": mode.pk,
                        "value": 1,
                    }
                ],
            },
        }

        url = reverse(
            'emissions:create_asset_baseline', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk}
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        baseline = Baseline.objects.get()
        assert response.data == BaselineDetailsSerializer(baseline).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:create_asset_baseline', kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0})
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)

        api_client = APIClient()

        url = reverse('emissions:create_asset_baseline', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:create_asset_baseline', kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateAssetBaselineApi:
    def test_should_update_asset_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.WINTER)

        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(baseline=baseline, phase=phase, mode=mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=phase, mode=mode, season=AssetSeason.WINTER)

        data = {
            "name": "Test baseline",
            "description": "Test description",
            "boilers_fuel_consumption_summer": 13,
            "boilers_fuel_consumption_winter": 7.5,
            "draft": True,
            "summer": {
                "transit": 0,
                "inputs": [
                    {
                        "phase": phase.pk,
                        "mode": mode.pk,
                        "value": 1,
                    }
                ],
            },
            "winter": {
                "transit": 0,
                "inputs": [
                    {
                        "phase": phase.pk,
                        "mode": mode.pk,
                        "value": 1,
                    }
                ],
            },
        }

        url = reverse(
            'emissions:update_asset_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        baseline.refresh_from_db()
        assert response.data == BaselineDetailsSerializer(baseline).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        baseline = BaselineFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": 0, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_asset_baseline',
            kwargs={"tenant_id": tenant_user.tenant_id, "asset_id": asset.pk, "baseline_id": 0},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:update_asset_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_asset_baseline',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestEmissionReductionInitiativeDetailsApi:
    def test_should_retrieve_emission_reduction_initiative_details(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        emission_reduction_initiative = EmissionReductionInitiativeFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": 0,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline, deleted=True)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": 0,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_user_from_other_tenant(self):
        tenant_user = TenantUserRelationFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_reduction_initiative_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateEmissionReductionInitiativeApi:
    def test_should_create_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.WINTER)

        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)

        BaselineInputFactory(baseline=baseline, phase=phase, mode=mode)

        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        data = {
            "name": "Test create emission reduction initiative",
            "description": "Test create emission reduction initiative description",
            "type": EmissionReductionInitiativeType.PRODUCTIVITY.value,
            "vendor": "Test create emission reduction initiative status",
            "deployment_date": datetime.date.today().isoformat(),
            "inputs": [
                {
                    "phase": phase.pk,
                    "mode": mode.pk,
                    "value": 1,
                }
            ],
            "transit": 0,
        }

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        emission_reduction_initiative = EmissionReductionInitiative.objects.get()
        assert response.data == EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory(deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": emission_management_plan.baseline.asset.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(UserFactory())

        url = reverse(
            'emissions:create_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateEmissionReductionInitiativeApi:
    def test_should_update_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)

        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode)
        BaselineInputFactory(baseline=baseline, phase=phase, mode=mode)

        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        EmissionReductionInitiativeInputFactory(
            phase=phase,
            mode=mode,
            emission_reduction_initiative=emission_reduction_initiative,
        )
        EmissionReductionInitiativeInputFactory(
            phase=transit_phase,
            mode=transit_mode,
            emission_reduction_initiative=emission_reduction_initiative,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        data = {
            "name": "Test update emission reduction initiative",
            "description": "Test update emission reduction initiative description",
            "type": EmissionReductionInitiativeType.PRODUCTIVITY.value,
            "vendor": "Test update emission reduction initiative status",
            "deployment_date": datetime.date.today().isoformat(),
            "inputs": [
                {
                    "phase": phase.pk,
                    "mode": mode.pk,
                    "value": 1,
                }
            ],
            "transit": 0,
        }

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        emission_reduction_initiative.refresh_from_db()
        assert response.data == EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": 0,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory(deleted=True)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": 0,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
            deleted=True,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_non_authenticated_user(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": "Authentication credentials were not provided."}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan,
        )

        api_client = APIClient()
        api_client.force_authenticate(UserFactory())

        url = reverse(
            'emissions:update_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": emission_management_plan.baseline.asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": "You do not have permission to perform this action."}


@pytest.mark.django_db
class TestEmissionManagementPlanDetailsApi:
    def test_should_retrieve_emission_management_plan_details(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == EmissionManagementPlanDetailsSerializer(emission_management_plan).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:emission_management_plan_details',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateEmissionManagementPlanApi:
    def test_should_create_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset, draft=False)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        data = {
            "name": "Test create emission management plan",
            "description": "Test create emission management plan description",
            "version": "1.0",
            "draft": True,
        }

        url = reverse(
            'emissions:create_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        emission_management_plan = EmissionManagementPlan.objects.get()
        assert response.data == EmissionManagementPlanDetailsSerializer(emission_management_plan).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        baseline = BaselineFactory(asset__tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:create_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:create_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateEmissionManagementPlanApi:
    def test_should_update_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        data = {
            "name": "Test update emission management plan",
            "description": "Test update emission management plan description",
            "version": "1.0",
            "draft": True,
        }

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        emission_management_plan.refresh_from_db()
        assert response.data == EmissionManagementPlanDetailsSerializer(emission_management_plan).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:update_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestActivateEmissionManagementPlanApi:
    def test_should_activate_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset, draft=False)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 200
        emission_management_plan.refresh_from_db()
        assert response.data == AssetDetailsSerializer.EmissionManagementPlanSerializer(emission_management_plan).data

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:activate_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDuplicateEmissionManagementPlanApi:
    def test_should_duplicate_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 201
        duplicated_emission_management_plan = EmissionManagementPlan.objects.last()
        assert (
            response.data
            == AssetDetailsSerializer.EmissionManagementPlanSerializer(duplicated_emission_management_plan).data
        )

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        emission_management_plan = EmissionManagementPlanFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'emissions:duplicate_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAllVesselTypeListApi:
    def test_should_retrieve_vessel_type_list(self):
        tenant_user = TenantUserRelationFactory()
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)
        VesselTypeFactory(tenant=tenant_user.tenant, deleted=True)
        VesselTypeFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:all_vessel_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AllVesselTypeListSerializer([vessel_type], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:all_vessel_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:all_vessel_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestHelicopterTypeListApi:
    def test_should_retrieve_helicopter_type_list(self):
        tenant_user = TenantUserRelationFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)
        HelicopterTypeFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:helicopter_type_list',
            kwargs={"tenant_id": tenant_user.tenant.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': HelicopterTypeListSerializer([helicopter_type], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:helicopter_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:helicopter_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateHelicopterTypeApi:
    def test_should_create_helicopter_type(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:create_helicopter_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
            },
        )

        data = {
            "type": "Helicopter Type",
            "fuel_density": 100,
            "co2_per_fuel": 100,
            "nox_per_fuel": 100,
            "fuel_consumption": 100,
            "fuel_cost": 100,
            "co2_tax": 100,
            "nox_tax": 100,
        }
        response = api_client.post(url, data=data)

        assert response.status_code == 201
        assert response.data == HelicopterTypeListSerializer(HelicopterType.objects.get()).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:create_helicopter_type', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:create_helicopter_type', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateHelicopterTypeApi:
    def test_should_update_helicopter_type(self):
        tenant_user = TenantUserRelationFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_helicopter_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )

        data = {
            "type": "Helicopter Type",
            "fuel_density": 100,
            "co2_per_fuel": 100,
            "nox_per_fuel": 100,
            "fuel_consumption": 100,
            "fuel_cost": 100,
            "co2_tax": 100,
            "nox_tax": 100,
        }
        response = api_client.put(url, data=data)

        assert response.status_code == 200
        helicopter_type.refresh_from_db()
        assert response.data == HelicopterTypeListSerializer(helicopter_type).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        url = reverse(
            'emissions:update_helicopter_type',
            kwargs={
                "tenant_id": tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        api_client = APIClient()

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:update_helicopter_type',
            kwargs={
                "tenant_id": tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAllHelicopterTypeListApi:
    def test_should_retrieve_helicopter_type_list(self):
        tenant_user = TenantUserRelationFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)
        HelicopterTypeFactory(tenant=tenant_user.tenant, deleted=True)
        HelicopterTypeFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:all_helicopter_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AllHelicopterTypeListSerializer([helicopter_type], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:all_helicopter_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:all_helicopter_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteEmissionManagementPlanApi:
    def test_should_delete_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": 0,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        asset = AssetFactory()
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)

        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:delete_emission_management_plan',
            kwargs={
                "tenant_id": asset.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_management_plan.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteEmissionReductionInitiative:
    def test_should_delete_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_non_existing_asset(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": 0,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": 0,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_management_plan(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": 0,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": 0,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_emission_reduction_initiative(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset, deleted=True
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(tenant=tenant)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset
        )

        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:delete_emission_reduction_initiative',
            kwargs={
                "tenant_id": tenant.pk,
                "asset_id": asset.pk,
                "baseline_id": emission_reduction_initiative.emission_management_plan.baseline.pk,
                "emission_management_plan_id": emission_reduction_initiative.emission_management_plan.pk,
                "emission_reduction_initiative_id": emission_reduction_initiative.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": "You do not have permission to perform this action."}


@pytest.mark.django_db
class TestDeleteHelicopterTypeApi:
    def test_should_delete_helicopter_type(self):
        tenant_user = TenantUserRelationFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_helicopter_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_deleted_helicopter_type(self):
        tenant_user = TenantUserRelationFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant, deleted=True)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_helicopter_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        url = reverse(
            'emissions:delete_helicopter_type',
            kwargs={
                "tenant_id": tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        api_client = APIClient()

        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:delete_helicopter_type',
            kwargs={
                "tenant_id": tenant.pk,
                "helicopter_type_id": helicopter_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestBaselinePhaseListApi:
    def test_should_retrieve_phase_list(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        custom_phase_with_phase = CustomPhaseFactory(asset=asset, phase__transit=False)
        custom_mode_with_mode = CustomModeFactory(asset=asset, mode__transit=False)
        custom_phase_without_phase = CustomPhaseFactory(asset=asset, phase=None)
        custom_mode_without_mode = CustomModeFactory(asset=asset, mode=None)
        BaselineInputFactory(
            baseline=baseline, phase=custom_phase_with_phase, mode=custom_mode_with_mode, season=AssetSeason.SUMMER
        )
        BaselineInputFactory(
            baseline=baseline, phase=custom_phase_with_phase, mode=custom_mode_with_mode, season=AssetSeason.WINTER
        )
        BaselineInputFactory(
            baseline=baseline,
            phase=custom_phase_without_phase,
            mode=custom_mode_without_mode,
            season=AssetSeason.SUMMER,
        )
        BaselineInputFactory(
            baseline=baseline,
            phase=custom_phase_without_phase,
            mode=custom_mode_without_mode,
            season=AssetSeason.WINTER,
        )
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.WINTER)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert (
            response.data
            == BaselinePhaseSerializer([custom_phase_with_phase, custom_phase_without_phase], many=True).data
        )

    @pytest.mark.parametrize("deleted_asset, deleted_baseline", ((True, False), (False, True)))
    def test_should_be_not_found_for_deleted_object(self, deleted_asset: bool, deleted_baseline: bool):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, deleted=deleted_asset)
        baseline = BaselineFactory(asset=asset, deleted=deleted_baseline)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_not_found_for_unknown_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory()
        baseline = BaselineFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()

        url = reverse(
            'emissions:baseline_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:baseline_phase_list',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestBaselineModeListApi:
    def test_should_retrieve_phase_list(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        custom_phase_with_phase = CustomPhaseFactory(asset=asset, phase__transit=False)
        custom_mode_with_mode = CustomModeFactory(asset=asset, mode__transit=False)
        custom_phase_without_phase = CustomPhaseFactory(asset=asset, phase=None)
        custom_mode_without_mode = CustomModeFactory(asset=asset, mode=None)
        BaselineInputFactory(
            baseline=baseline, phase=custom_phase_with_phase, mode=custom_mode_with_mode, season=AssetSeason.SUMMER
        )
        BaselineInputFactory(
            baseline=baseline, phase=custom_phase_with_phase, mode=custom_mode_with_mode, season=AssetSeason.WINTER
        )
        BaselineInputFactory(
            baseline=baseline,
            phase=custom_phase_without_phase,
            mode=custom_mode_without_mode,
            season=AssetSeason.SUMMER,
        )
        BaselineInputFactory(
            baseline=baseline,
            phase=custom_phase_without_phase,
            mode=custom_mode_without_mode,
            season=AssetSeason.WINTER,
        )
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, season=AssetSeason.WINTER)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2
        assert (
            response.data == BaselineModeSerializer([custom_mode_with_mode, custom_mode_without_mode], many=True).data
        )

    @pytest.mark.parametrize("deleted_asset, deleted_baseline", ((True, False), (False, True)))
    def test_should_be_not_found_for_deleted_object(self, deleted_asset: bool, deleted_baseline: bool):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant, deleted=deleted_asset)
        baseline = BaselineFactory(asset=asset, deleted=deleted_baseline)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_not_found_for_unknown_baseline(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory()
        baseline = BaselineFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:baseline_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant_user = TenantUserRelationFactory()
        asset = AssetFactory(tenant=tenant_user.tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()

        url = reverse(
            'emissions:baseline_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        asset = AssetFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:baseline_mode_list',
            kwargs={"tenant_id": tenant.pk, "asset_id": asset.pk, "baseline_id": baseline.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestMaterialTypeListApi:
    def test_should_retrieve_material_type_list(self):
        tenant_user = TenantUserRelationFactory()
        material_type = MaterialTypeFactory(tenant=tenant_user.tenant)
        MaterialTypeFactory(tenant=tenant_user.tenant, deleted=True)
        MaterialTypeFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:material_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': MaterialTypeListSerializer([material_type], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:material_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:material_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteMaterialTypeApi:
    def test_should_delete_material_type(self):
        tenant_user = TenantUserRelationFactory()
        material_type = MaterialTypeFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_non_existing_material_type(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": 999,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_material_type(self):
        tenant_user = TenantUserRelationFactory()
        material_type = MaterialTypeFactory(tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        material_type = MaterialTypeFactory(tenant=tenant)
        url = reverse(
            'emissions:delete_material_type',
            kwargs={
                "tenant_id": tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        api_client = APIClient()

        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        material_type = MaterialTypeFactory(tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:delete_material_type',
            kwargs={
                "tenant_id": tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateMaterialTypeApi:
    def test_should_create_material_type(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:create_material_type', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.post(
            url, data={"category": MaterialCategory.STEEL, "type": "Steel", "unit": "kg", "co2": 100.5}
        )

        assert response.status_code == 201
        assert response.data == MaterialTypeListSerializer(MaterialType.objects.get()).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:create_material_type', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:create_material_type', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateMaterialTypeApi:
    def test_should_update_material_type(self):
        tenant_user = TenantUserRelationFactory()
        material_type = MaterialTypeFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.put(url, data={"type": "Steel", "unit": "kg", "co2": 100.5})

        assert response.status_code == 200
        material_type.refresh_from_db()
        assert response.data == MaterialTypeListSerializer(material_type).data

    def test_should_be_not_found_for_non_existing_material_type(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": 999,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_deleted_material_type(self):
        tenant_user = TenantUserRelationFactory()
        material_type = MaterialTypeFactory(tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:update_material_type',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        material_type = MaterialTypeFactory(tenant=tenant)
        url = reverse(
            'emissions:update_material_type',
            kwargs={
                "tenant_id": tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        api_client = APIClient()

        response = api_client.put(url)

        assert response.status_code == 403
        assert response

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        material_type = MaterialTypeFactory(tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'emissions:update_material_type',
            kwargs={
                "tenant_id": tenant.pk,
                "material_type_id": material_type.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestAllMaterialTypeListApi:
    def test_should_retrieve_all_material_type_list(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        material_type = MaterialTypeFactory(tenant=tenant_user.tenant)
        MaterialTypeFactory(tenant=tenant_user.tenant, deleted=True)
        MaterialTypeFactory()

        url = reverse('emissions:all_material_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == AllMaterialTypeListSerializer([material_type], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:all_material_type_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:all_material_type_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}

    @pytest.mark.parametrize('role', [UserRole.OPERATOR, UserRole.ASSET_MANAGER])
    def test_should_be_forbidden_for_non_admin_user(self, role: UserRole):
        tenant_user = TenantUserRelationFactory(user__role=role)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:all_material_type_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
