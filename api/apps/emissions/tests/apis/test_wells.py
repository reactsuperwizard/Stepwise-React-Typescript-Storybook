import datetime
from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.emissions.factories import (
    AssetFactory,
    BaseHelicopterUseFactory,
    BaselineFactory,
    BaseVesselUseFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    EmissionReductionInitiativeFactory,
    HelicopterTypeFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    TargetCO2Factory,
    VesselTypeFactory,
    WellNameFactory,
)
from apps.emissions.factories.wells import BaseCO2Factory, BaselineCO2Factory, TargetCO2ReductionFactory
from apps.emissions.models import CompleteHelicopterUse, PlannedHelicopterUse, WellName
from apps.emissions.models.wells import BaseCO2, BaselineCO2, TargetCO2, TargetCO2Reduction
from apps.emissions.serializers import WellCO2EmissionSerializer, WellNameListSerializer
from apps.emissions.serializers.wells import WellEmissionReductionSerializer
from apps.emissions.services import get_co2_emissions, get_emission_reductions
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory
from apps.tenants.models import UserRole
from apps.wells.factories import WellPlannerFactory, WellPlannerPlannedStepFactory
from apps.wells.models import WellPlanner, WellPlannerWizardStep
from apps.wells.serializers import WellPlannerDetailsSerializer, WellPlannerListSerializer


@pytest.mark.django_db
class TestDeleteWellApi:
    def test_should_delete_well(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )

        response = api_client.delete(url)

        assert response.status_code == 204
        assert not WellPlanner.objects.live().exists()

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )

        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:delete_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": 1})

        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)

        url = reverse('emissions:delete_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        api_client = APIClient()

        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:delete_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}

    @pytest.mark.parametrize("user_role", (UserRole.OPERATOR, UserRole.ASSET_MANAGER))
    def test_should_be_forbidden_for_non_admin_user(self, user_role: UserRole):
        tenant_user = TenantUserRelationFactory(user__role=user_role)
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:delete_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDuplicateWellApi:
    def test_should_duplicate_well(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )
        response = api_client.post(url)

        assert response.status_code == 201
        well_planner_copy = WellPlanner.objects.order_by('id').last()

        assert response.data == WellPlannerListSerializer(well_planner_copy).data
        assert WellPlanner.objects.count() == 2

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        WellPlannerFactory(asset__tenant=tenant_user.tenant)
        WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:duplicate_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": 9999})
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)

        url = reverse('emissions:duplicate_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        api_client = APIClient()

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:duplicate_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}

    @pytest.mark.parametrize("user_role", (UserRole.OPERATOR, UserRole.ASSET_MANAGER))
    def test_should_be_forbidden_for_non_admin_user(self, user_role: UserRole):
        tenant_user = TenantUserRelationFactory(user__role=user_role)
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'emissions:duplicate_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk}
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateWellApi:
    def test_should_create_well(self, well_data: dict):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)
        asset = AssetFactory(tenant=tenant_user.tenant, draft=False)
        name = WellNameFactory(tenant=tenant_user.tenant)
        BaselineFactory(asset=asset, active=True, draft=False)

        data = {
            "asset": asset.pk,
            "name": name.pk,
            **well_data,
        }

        url = reverse('emissions:create_well', kwargs={"tenant_id": tenant_user.tenant_id})
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        well_planner = WellPlanner.objects.get()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()

        url = reverse('emissions:create_well', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:create_well', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateWellApi:
    def test_should_update_well(self, well_data: dict):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__draft=False,
            asset__tenant=tenant_user.tenant,
            current_step=WellPlannerWizardStep.WELL_PLANNING,
        )
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "asset": well_planner.asset.pk,
            "name": well_planner.name.pk,
            **well_data,
        }

        url = reverse(
            'emissions:update_well', kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk}
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'emissions:update_well', kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk}
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('emissions:update_well', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": 9999})
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(
            asset__draft=False, asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        api_client = APIClient()

        url = reverse('emissions:update_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(
            asset__draft=False, asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:update_well', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellNameListApi:
    def test_should_retrieve_well_name_list(self):
        tenant_user = TenantUserRelationFactory()
        first_well_name = WellNameFactory(tenant=tenant_user.tenant, name="1603/10-B-1")
        second_well_name = WellNameFactory(tenant=tenant_user.tenant, name="1503/10-A-1")
        WellNameFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('emissions:well_name_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == WellNameListSerializer([second_well_name, first_well_name], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        url = reverse('emissions:well_name_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('emissions:well_name_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateWellNameApi:
    def test_should_create_well_name(self, well_data: dict):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)
        data = {
            "name": "Well name",
        }

        url = reverse('emissions:create_well_name', kwargs={"tenant_id": tenant_user.tenant_id})
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        well_name = WellName.objects.get()
        assert response.data == WellNameListSerializer(well_name).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()

        url = reverse('emissions:create_well_name', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        api_client.force_authenticate(user=user)

        url = reverse('emissions:create_well_name', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path, current_step",
    (
        (
            "emissions:create_well_planned_vessel_use",
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "emissions:create_well_complete_vessel_use",
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
    ),
)
class TestCreateWellVesselUseApis:
    def test_should_create_well_vessel_use_api(
        self, path: str, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 201
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(
        self, path: str, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(
        self, path: str, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_type = VesselTypeFactory()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.post(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self, path: str, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self, path: str, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,id_parameter_name,VesselUseFactory,current_step",
    (
        (
            "emissions:update_well_planned_vessel_use",
            "planned_vessel_use_id",
            PlannedVesselUseFactory,
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "emissions:update_well_complete_vessel_use",
            "complete_vessel_use_id",
            CompleteVesselUseFactory,
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
    ),
)
class TestUpdateWellVesselUseApis:
    def test_should_update_well_vessel_use_api(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)
        vessel_use = VesselUseFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        vessel_use = VesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_use = VesselUseFactory(
            well_planner__asset__tenant=tenant_user.tenant, well_planner__current_step=current_step
        )
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 404

    def test_should_be_not_found_for_non_existing_vessel_use(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: 9999,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 404

    def test_should_be_forbidden_for_anonymous_user(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        planned_vessel_use = PlannedVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: planned_vessel_use.pk,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
        vessel_use_data: dict,
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        planned_vessel_use = PlannedVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: planned_vessel_use.pk,
            },
        )
        response = api_client.put(url, {"vessel_type": vessel_type.pk, **vessel_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,id_parameter_name,VesselUseFactory,current_step",
    (
        (
            "emissions:delete_well_planned_vessel_use",
            "planned_vessel_use_id",
            PlannedVesselUseFactory,
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "emissions:delete_well_complete_vessel_use",
            "complete_vessel_use_id",
            CompleteVesselUseFactory,
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
    ),
)
class TestDeleteWellVesselUseApis:
    def test_should_delete_well_vessel_use(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        vessel_use = VesselUseFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        vessel_use = VesselUseFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404

    def test_should_be_not_found_for_non_existing_well(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        vessel_use = VesselUseFactory(
            well_planner__asset__tenant=tenant_user.tenant, well_planner__current_step=current_step
        )

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404

    def test_should_be_not_found_for_non_existing_vessel_use(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: 9999,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404

    def test_should_be_forbidden_for_anonymous_user(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        vessel_use = VesselUseFactory(well_planner=well_planner)

        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        path: str,
        id_parameter_name: str,
        VesselUseFactory: type[BaseVesselUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        vessel_use = VesselUseFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: vessel_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateWellPlannedStartDateApi:
    def test_should_update_well_planned_start_date(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"planned_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "emissions:update_well_planned_start_date",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "emissions:update_well_planned_start_date",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(self):
        tenant_user = TenantUserRelationFactory()

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"planned_start_date": date(2022, 6, 1).isoformat()}
        url = reverse(
            "emissions:update_well_planned_start_date",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()

        data = {"planned_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "emissions:update_well_planned_start_date",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        data = {"planned_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "emissions:update_well_planned_start_date",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,current_step",
    (
        ("emissions:create_well_planned_helicopter_use", WellPlannerWizardStep.WELL_PLANNING),
        ("emissions:create_well_complete_helicopter_use", WellPlannerWizardStep.WELL_REVIEWING),
    ),
)
class TestCreateHelicopterUseApi:
    def test_should_create_helicopter_use(
        self, path: str, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"helicopter_type": helicopter_type.pk, **helicopter_use_data}
        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(
        self, path: str, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(
        self, path: str, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.post(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self, path: str, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self, path: str, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,id_parameter_name,HelicopterUseFactory,current_step",
    (
        (
            "emissions:update_well_planned_helicopter_use",
            "planned_helicopter_use_id",
            PlannedHelicopterUseFactory,
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "emissions:update_well_complete_helicopter_use",
            "complete_helicopter_use_id",
            CompleteHelicopterUseFactory,
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
    ),
)
class TestUpdateWellPlannedHelicopterUseApi:
    def test_should_update_helicopter_use(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        helicopter_use = HelicopterUseFactory(
            well_planner=well_planner,
        )
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"helicopter_type": helicopter_type.pk, **helicopter_use_data}
        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.put(url, data)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        helicopter_use = HelicopterUseFactory(well_planner=well_planner)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.put(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        helicopter_use = HelicopterUseFactory(
            well_planner__asset__tenant=tenant_user.tenant, well_planner__current_step=current_step
        )
        helicopter_type = HelicopterTypeFactory(tenant=tenant_user.tenant)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.put(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_helicopter_use(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: 9999,
            },
        )
        response = api_client.put(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)
        helicopter_use = HelicopterUseFactory(
            well_planner=well_planner,
        )
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.put(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
        helicopter_use_data: dict,
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_use = HelicopterUseFactory(
            well_planner=well_planner,
        )
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.put(url, {"helicopter_type": helicopter_type.pk, **helicopter_use_data})

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,id_parameter_name,HelicopterUseFactory,current_step",
    (
        (
            "emissions:delete_well_planned_helicopter_use",
            "planned_helicopter_use_id",
            PlannedHelicopterUseFactory,
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "emissions:delete_well_complete_helicopter_use",
            "complete_helicopter_use_id",
            CompleteHelicopterUseFactory,
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
    ),
)
class TestDeleteWellHelicopterUseApis:
    def test_should_delete_well_helicopter_use(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        helicopter_use = HelicopterUseFactory(
            well_planner=well_planner,
        )
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

        assert not PlannedHelicopterUse.objects.filter(pk=helicopter_use.pk).exists()
        assert not CompleteHelicopterUse.objects.filter(pk=helicopter_use.pk).exists()

    def test_should_be_not_found_for_deleted_well(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        helicopter_use = HelicopterUseFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        helicopter_use = HelicopterUseFactory(
            well_planner__asset__tenant=tenant_user.tenant, well_planner__current_step=current_step
        )

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_helicopter_use(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: 9999,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_use = HelicopterUseFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        path: str,
        id_parameter_name: str,
        HelicopterUseFactory: type[BaseHelicopterUseFactory],
        current_step: WellPlannerWizardStep,
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        helicopter_use = HelicopterUseFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: helicopter_use.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,co2_factory,co2_model",
    (
        ("emissions:well_target_co2_emissions", TargetCO2Factory, TargetCO2),
        ("emissions:well_baseline_co2_emissions", BaselineCO2Factory, BaselineCO2),
    ),
)
class TestCO2EmissionsApi:
    def test_should_retrieve_co2_emissions(
        self, path: str, co2_factory: type[BaseCO2Factory], co2_model: type[BaseCO2]
    ):
        tenant_user = TenantUserRelationFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        start = datetime.datetime(year=2022, month=1, day=1, hour=0, minute=0)
        co2_factory(
            planned_step__well_planner=well_plan,
            datetime=start,
        )
        co2_factory(
            planned_step__well_planner=well_plan,
            datetime=start + datetime.timedelta(hours=8),
        )
        co2_factory(
            planned_step__well_planner=well_plan,
            datetime=start + datetime.timedelta(days=1),
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(
            reverse(path, kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_plan.pk})
        )

        assert response.status_code == 200
        assert (
            response.data
            == WellCO2EmissionSerializer(get_co2_emissions(well_planner=well_plan, co2_model=co2_model), many=True).data
        )

    def test_should_be_not_found_for_unknown_well_plan(
        self, path: str, co2_factory: type[BaseCO2Factory], co2_model: type[BaseCO2]
    ):
        tenant_user = TenantUserRelationFactory()
        well_plan = WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(
            reverse(path, kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_plan.pk})
        )

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self, path: str, co2_factory: type[BaseCO2Factory], co2_model: type[BaseCO2]
    ):
        tenant = TenantFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        response = api_client.get(reverse(path, kwargs={"tenant_id": tenant.pk, "well_planner_id": well_plan.pk}))

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self, path: str, co2_factory: type[BaseCO2Factory], co2_model: type[BaseCO2]
    ):
        tenant = TenantFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        response = api_client.get(reverse(path, kwargs={"tenant_id": tenant.pk, "well_planner_id": well_plan.pk}))

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellTargetCO2EmissionReductionsApi:
    def test_should_retrieve_emission_reductions(self):
        tenant_user = TenantUserRelationFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        phase = WellPlannerPlannedStepFactory(improved_duration=0.5, well_planner=well_plan)
        emission_reduction_initiative = EmissionReductionInitiativeFactory()
        TargetCO2ReductionFactory(
            target__planned_step=phase,
            emission_reduction_initiative=emission_reduction_initiative,
            target__datetime=well_plan.planned_start_date + datetime.timedelta(days=0.5),
            value=10,
        )

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(
            reverse(
                'emissions:well_target_co2_emission_reductions',
                kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_plan.pk},
            )
        )

        assert response.status_code == 200
        assert (
            response.data
            == WellEmissionReductionSerializer(
                get_emission_reductions(well_plan=well_plan, reduction_model=TargetCO2Reduction), many=True
            ).data
        )

    def test_should_be_not_found_for_unknown_well_plan(self):
        tenant_user = TenantUserRelationFactory()
        well_plan = WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(
            reverse(
                'emissions:well_target_co2_emission_reductions',
                kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_plan.pk},
            )
        )

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        response = api_client.get(
            reverse(
                'emissions:well_target_co2_emission_reductions',
                kwargs={"tenant_id": tenant.pk, "well_planner_id": well_plan.pk},
            )
        )

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        well_plan = WellPlannerFactory(asset__tenant=tenant)
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        response = api_client.get(
            reverse(
                'emissions:well_target_co2_emission_reductions',
                kwargs={"tenant_id": tenant.pk, "well_planner_id": well_plan.pk},
            )
        )

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
