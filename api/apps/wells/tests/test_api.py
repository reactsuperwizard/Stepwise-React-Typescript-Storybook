from datetime import date, datetime, timedelta

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.emissions.factories import (
    BaselineInputFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionReductionInitiativeFactory,
    EmissionReductionInitiativeInputFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
)
from apps.emissions.models.assets import MaterialCategory
from apps.projects.factories import PlanWellRelationFactory
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory
from apps.wells.factories import (
    BaseWellPlannerStepFactory,
    ConceptWellFactory,
    CustomWellFactory,
    WellPlannerCompleteStepFactory,
    WellPlannerFactory,
    WellPlannerPlannedStepFactory,
    WellReferenceMaterialFactory,
)
from apps.wells.models import (
    AssetSeason,
    CustomWell,
    WellPlannerCompleteStep,
    WellPlannerPlannedStep,
    WellPlannerWizardStep,
)
from apps.wells.serializers import (
    ConceptWellDetailsSerializer,
    ConceptWellListSerializer,
    CustomWellDetailsSerializer,
    CustomWellListSerializer,
    WellPlannerDetailsSerializer,
    WellPlannerListSerializer,
    WellPlannerModeListSerializer,
    WellPlannerPhaseListSerializer,
    WellReferenceMaterialSerializer,
)
from apps.wells.tests.fixtures import (
    CUSTOM_WELL_DRAFT_DATA,
    CUSTOM_WELL_PUBLIC_DATA,
    WELL_PLANNER_COMPLETE_STEP_DATA,
    WELL_PLANNER_PLANNED_STEP_DATA,
)

from ...emissions.factories.assets import ExternalEnergySupplyFactory, MaterialTypeFactory
from ...emissions.serializers import EmissionReductionInitiativeListSerializer
from ...monitors.factories import MonitorFunctionFactory, MonitorFunctionValueFactory
from ...monitors.models import MonitorFunctionType


@pytest.mark.django_db
class TestCustomWellListApi:
    def test_should_retrieve_custom_well_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('wells:custom_well_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        well = CustomWellFactory(tenant=tenant_user.tenant, creator=tenant_user.user)
        CustomWellFactory()

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': CustomWellListSerializer(
                [
                    well,
                ],
                many=True,
            ).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('wells:custom_well_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('wells:custom_well_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestConceptWellListApi:
    def test_should_retrieve_concept_well_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        well = ConceptWellFactory()
        url = reverse('wells:concept_well_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "count": 1,
            "previous": None,
            "next": None,
            "results": [ConceptWellListSerializer(well).data],
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        ConceptWellFactory()
        url = reverse('wells:concept_well_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        ConceptWellFactory()
        url = reverse('wells:concept_well_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateCustomWellApi:
    @pytest.mark.parametrize("data", (CUSTOM_WELL_DRAFT_DATA, CUSTOM_WELL_PUBLIC_DATA))
    def test_should_create_custom_well(self, data):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()

        url = reverse('wells:create_custom_well', kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        well = CustomWell.objects.get()
        assert response.data == {**CustomWellDetailsSerializer(well).data, **data}

    def test_should_provide_all_data_to_create_public_well(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()

        url = reverse('wells:create_custom_well', kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data={**CUSTOM_WELL_DRAFT_DATA, "draft": False}, format='json')

        assert response.status_code == 400

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('wells:create_custom_well', kwargs={"tenant_id": tenant.pk})

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('wells:create_custom_well', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateCustomWellApi:
    @pytest.mark.parametrize("data", (CUSTOM_WELL_DRAFT_DATA, CUSTOM_WELL_PUBLIC_DATA))
    def test_should_update_custom_well(self, data):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        well = CustomWellFactory(tenant=tenant_user.tenant)
        url = reverse('wells:update_custom_well', kwargs={"tenant_id": tenant_user.tenant_id, "well_id": well.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        well.refresh_from_db()
        assert response.data == {**CustomWellDetailsSerializer(well).data, **data}

    def test_should_provide_all_data_to_update_public_custom_well(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        well = CustomWellFactory(tenant=tenant_user.tenant)
        url = reverse('wells:update_custom_well', kwargs={"tenant_id": tenant_user.tenant_id, "well_id": well.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data={**CUSTOM_WELL_DRAFT_DATA, "draft": False}, format='json')

        assert response.status_code == 400

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        well = CustomWellFactory()
        url = reverse('wells:update_custom_well', kwargs={"tenant_id": well.tenant_id, "well_id": well.pk})

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        well = CustomWellFactory()
        user = UserFactory()
        url = reverse('wells:update_custom_well', kwargs={"tenant_id": well.tenant_id, "well_id": well.pk})
        api_client.force_authenticate(user)

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestConceptWellDetailsApi:
    def test_should_retrieve_concept_well_details(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        well = ConceptWellFactory()
        url = reverse('wells:concept_well_details', kwargs={"tenant_id": tenant_user.tenant_id, "well_id": well.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == ConceptWellDetailsSerializer(well).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        well = ConceptWellFactory()
        url = reverse('wells:concept_well_details', kwargs={"tenant_id": tenant.pk, "well_id": well.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        well = ConceptWellFactory()
        user = UserFactory()
        tenant = TenantFactory()
        url = reverse('wells:concept_well_details', kwargs={"tenant_id": tenant.pk, "well_id": well.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCustomWellDetailsApi:
    def test_should_retrieve_custom_well_details(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        well = CustomWellFactory(tenant=tenant_user.tenant)
        url = reverse('wells:custom_well_details', kwargs={"tenant_id": tenant_user.tenant_id, "well_id": well.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == CustomWellDetailsSerializer(well).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        well = CustomWellFactory(tenant=tenant)
        url = reverse('wells:custom_well_details', kwargs={"tenant_id": tenant.pk, "well_id": well.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        well = CustomWellFactory()
        user = UserFactory()
        tenant = TenantFactory()
        url = reverse('wells:custom_well_details', kwargs={"tenant_id": tenant.pk, "well_id": well.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteCustomWellApi:
    def test_should_delete_well(self):
        api_client = APIClient()
        tenant = TenantFactory()
        well = CustomWellFactory(tenant=tenant)
        PlanWellRelationFactory(well=well)
        tenant_user = TenantUserRelationFactory(tenant=tenant)
        url = reverse(
            'wells:delete_custom_well',
            kwargs={"tenant_id": tenant.pk, "well_id": well.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.delete(url)

        assert response.status_code == 204
        with pytest.raises(CustomWell.DoesNotExist):
            well.refresh_from_db()

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        well = CustomWellFactory(tenant=tenant)
        url = reverse(
            'wells:delete_custom_well',
            kwargs={"tenant_id": tenant.pk, "well_id": well.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        well = CustomWellFactory(tenant=tenant)
        url = reverse(
            'wells:delete_custom_well',
            kwargs={"tenant_id": tenant.pk, "well_id": well.pk},
        )
        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerDetailsApi:
    def test_should_retrieve_well_planner_details(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        WellPlannerPlannedStepFactory(well_planner=well_planner)
        WellPlannerCompleteStepFactory(well_planner=well_planner)
        PlannedVesselUseFactory(well_planner=well_planner)
        PlannedHelicopterUseFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert len(response.data['planned_vessel_uses']) == 1
        assert len(response.data["planned_helicopter_uses"]) == 1
        assert len(response.data['planned_steps']) == 1
        assert len(response.data['complete_steps']) == 1

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_details', kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": 9999}
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_different_tenant(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory()
        api_client = APIClient()

        url = reverse('wells:well_planner_details', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('wells:well_planner_details', kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateWellPlannerPlannedStepApi:
    def test_should_create_well_planner_planned_step(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        season = AssetSeason.SUMMER
        BaselineInputFactory(baseline=well_planner.baseline, phase=phase, mode=mode, season=season)

        cement = MaterialTypeFactory(tenant=tenant_user.tenant, category=MaterialCategory.CEMENT)
        steel = MaterialTypeFactory(tenant=tenant_user.tenant, category=MaterialCategory.STEEL)
        (
            emission_reduction_initiative_1,
            emission_reduction_initiative_2,
        ) = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            **WELL_PLANNER_PLANNED_STEP_DATA,
            "phase": phase.pk,
            "mode": mode.pk,
            "season": season,
            "emission_reduction_initiatives": [emission_reduction_initiative_1.pk, emission_reduction_initiative_2.pk],
            "materials": [
                {
                    "material_type": cement.pk,
                    "quantity": 100,
                    "quota": False,
                },
                {
                    "material_type": steel.pk,
                    "quantity": 100,
                    "quota": True,
                },
            ],
        }

        url = reverse(
            'wells:create_well_planner_planned_step',
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert len(response.data['planned_steps']) == 1

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:create_well_planner_planned_step',
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:create_well_planner_planned_step',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": 9999},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()

        url = reverse(
            'wells:create_well_planner_planned_step',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:create_well_planner_planned_step',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateWellPlannerPlannedStepApi:
    def test_should_update_well_planner_planned_step(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_PLANNED_STEP_DATA["season"]
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            **WELL_PLANNER_PLANNED_STEP_DATA,
            "phase": phase.pk,
            "mode": mode.pk,
            "emission_reduction_initiatives": [],
            "materials": [],
        }

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner__asset__tenant=tenant_user.tenant,
            well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING,
        )

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": 9999,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.put(url, data=WELL_PLANNER_PLANNED_STEP_DATA, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": 9999,
            },
        )
        response = api_client.put(url, data=WELL_PLANNER_PLANNED_STEP_DATA, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:update_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteWellPlannerPlannedStepApi:
    def test_should_delete_well_planner_planned_step(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not WellPlannerPlannedStep.objects.filter(pk=planned_step.pk).exists()

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner__asset__tenant=tenant_user.tenant,
            well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING,
        )

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": 9999,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:delete_well_planner_planned_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerPlannedCo2Api:
    def test_should_retrieve_well_planner_planned_co2(self):
        tenant_user = TenantUserRelationFactory()

        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            duration=7,
            improved_duration=1,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        emission_reduction_initiative_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
            phase=planned_step.phase,
            mode=planned_step.mode,
        )
        planned_step.emission_reduction_initiatives.add(
            emission_reduction_initiative_input.emission_reduction_initiative
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)
        expected_response = [
            {
                "date": datetime.combine(date.today(), datetime.min.time()).isoformat() + 'Z',
                "phase": {
                    "id": planned_step.phase.pk,
                    "name": planned_step.phase.name,
                    "color": "#FFFFFF",
                },
                "mode": {
                    "id": planned_step.mode.pk,
                    "name": planned_step.mode.name,
                },
                "rig": 0.0,
                "vessels": 0.0,
                "helicopters": 0.0,
                "external_energy_supply": 0.0,
                "cement": 0.0,
                "steel": 0.0,
                "step": dict(id=planned_step.pk),
                "emission_reduction_initiatives": [
                    {
                        "id": emission_reduction_initiative_input.emission_reduction_initiative_id,
                        "value": 0.0,
                    }
                ],
            },
        ]

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_planned_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_planned_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerPlannedCo2SavedApi:
    def test_should_retrieve_well_planner_planned_co2_saved(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            duration=1,
            waiting_on_weather=100,
            improved_duration=1,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        emission_reduction_initiative_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
            phase=planned_step.phase,
            mode=planned_step.mode,
        )
        planned_step.emission_reduction_initiatives.add(
            emission_reduction_initiative_input.emission_reduction_initiative
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2_saved',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)
        expected_response = [
            {
                "date": (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=1)).isoformat() + 'Z',
                "rig": 0.0,
                "vessels": 0.0,
                "helicopters": 0.0,
                "external_energy_supply": 0.0,
                "cement": 0.0,
                "steel": 0.0,
                "emission_reduction_initiatives": [
                    {
                        "id": emission_reduction_initiative_input.emission_reduction_initiative_id,
                        "value": 0.0,
                    }
                ],
            },
        ]

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2_saved',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_co2_saved',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_planned_co2_saved',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_planned_co2_saved',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerPlannedSummaryApi:
    def test_should_retrieve_well_planner_planned_summary(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            duration=2,
            improved_duration=1,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        emission_reduction_initiative_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
            phase=planned_step.phase,
            mode=planned_step.mode,
        )
        planned_step.emission_reduction_initiatives.add(
            emission_reduction_initiative_input.emission_reduction_initiative
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)
        expected_response = {
            "total_baseline": 0,
            "total_target": 0,
            "total_improved_duration": 1.0,
        }

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_planned_summary',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_planned_summary',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCompleteWellPlannerPlannedApi:
    def test_should_complete_well_planner_planning(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_planned',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        well_planner.refresh_from_db()
        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert len(response.data['complete_steps']) == 1

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_planned',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_planned',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()

        url = reverse(
            'wells:complete_well_planner_planned',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_PLANNING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:complete_well_planner_planned',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateWellPlannerCompleteStepApi:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_create_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        season = AssetSeason.SUMMER
        BaselineInputFactory(baseline=well_planner.baseline, phase=phase, mode=mode, season=season)

        cement = MaterialTypeFactory(tenant=tenant_user.tenant, category=MaterialCategory.CEMENT)
        steel = MaterialTypeFactory(tenant=tenant_user.tenant, category=MaterialCategory.STEEL)
        (
            emission_reduction_initiative_1,
            emission_reduction_initiative_2,
        ) = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            **WELL_PLANNER_COMPLETE_STEP_DATA,
            "phase": phase.pk,
            "mode": mode.pk,
            "season": season,
            "emission_reduction_initiatives": [emission_reduction_initiative_1.pk, emission_reduction_initiative_2.pk],
            "materials": [
                {
                    "material_type": cement.pk,
                    "quantity": 100,
                    "quota": False,
                },
                {
                    "material_type": steel.pk,
                    "quantity": 100,
                    "quota": True,
                },
            ],
        }

        url = reverse(
            'wells:create_well_planner_complete_step',
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert len(response.data['complete_steps']) == 1

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:create_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:create_well_planner_complete_step',
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": 9999},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()

        url = reverse(
            'wells:create_well_planner_complete_step',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:create_well_planner_complete_step',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateWellPlannerCompleteStepApi:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_update_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_COMPLETE_STEP_DATA["season"]
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            **WELL_PLANNER_COMPLETE_STEP_DATA,
            "phase": phase.pk,
            "mode": mode.pk,
            "emission_reduction_initiatives": [],
            "materials": [],
        }

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": 9999,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        complete_step = WellPlannerCompleteStepFactory(
            well_planner__asset__tenant=tenant_user.tenant,
            well_planner__current_step=WellPlannerWizardStep.WELL_REVIEWING,
        )

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": 9999,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.put(url, data=WELL_PLANNER_COMPLETE_STEP_DATA, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": 9999,
            },
        )
        response = api_client.put(url, data=WELL_PLANNER_COMPLETE_STEP_DATA, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:update_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteWellPlannerCompleteStepApi:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_delete_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 204
        assert not WellPlannerCompleteStep.objects.filter(pk=well_planner.pk).exists()

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": complete_step.well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        complete_step = WellPlannerCompleteStepFactory(
            well_planner__asset__tenant=tenant_user.tenant,
            well_planner__current_step=WellPlannerWizardStep.WELL_REVIEWING,
        )

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": 9999,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": 9999,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:delete_well_planner_complete_step',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_complete_step_id": complete_step.pk,
            },
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestApproveWellPlannerCompleteStepsApi:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_approve_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=False)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:approve_well_planner_complete_steps',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=dict(complete_steps=[complete_step.pk]))

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert response.data['complete_steps'][0]['approved']

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:approve_well_planner_complete_steps',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:approve_well_planner_complete_steps',
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "well_planner_id": 9999,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:approve_well_planner_complete_steps',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=dict(complete_steps=[complete_step.pk]))

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:approve_well_planner_complete_steps',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=dict(complete_steps=[complete_step.pk]))

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCompleteWellPlannerCompleteApi:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_complete_well_planner_complete(self, current_step: WellPlannerWizardStep):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_complete',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 200
        well_planner.refresh_from_db()
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_complete',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:complete_well_planner_complete',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()

        url = reverse(
            'wells:complete_well_planner_complete',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:complete_well_planner_complete',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerMeasuredCo2Api:
    def test_should_retrieve_well_planner_measured_co2(self):
        tenant_user = TenantUserRelationFactory()

        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        complete_step = WellPlannerCompleteStepFactory(
            well_planner=well_planner,
            duration=1,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(baseline__asset=well_planner.asset, phase=complete_step.phase, value=0)
        MonitorFunctionValueFactory(
            monitor_function__vessel=well_planner.asset.vessel,
            monitor_function__type=MonitorFunctionType.CO2_EMISSION,
            value=0,
        )
        emission_reduction_initiative_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative__emission_management_plan=well_planner.emission_management_plan,
            phase=complete_step.phase,
            mode=complete_step.mode,
        )
        complete_step.emission_reduction_initiatives.add(
            emission_reduction_initiative_input.emission_reduction_initiative
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_measured_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)
        expected_response = [
            {
                "date": datetime.combine(well_planner.actual_start_date, datetime.min.time()).isoformat() + 'Z',
                "phase": {
                    "id": complete_step.phase.pk,
                    "name": complete_step.phase.name,
                    "color": "#FFFFFF",
                },
                "mode": {
                    "id": complete_step.mode.pk,
                    "name": complete_step.mode.name,
                },
                "rig": 0.0,
                "vessels": 0.0,
                "helicopters": 0.0,
                "external_energy_supply": 0.0,
                "cement": 0.0,
                "steel": 0.0,
                "step": dict(id=complete_step.pk),
                "emission_reduction_initiatives": [
                    {
                        "id": emission_reduction_initiative_input.emission_reduction_initiative_id,
                        "value": 0.0,
                    }
                ],
            },
        ]

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_measured_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_measured_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_measured_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_measured_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,monitor_function_type",
    (
        ("wells:well_planner_measured_wind_speed", MonitorFunctionType.WIND_SPEED),
        ("wells:well_planner_measured_air_temperature", MonitorFunctionType.AIR_TEMPERATURE),
        ("wells:well_planner_measured_wave_heave", MonitorFunctionType.WAVE_HEAVE),
    ),
)
class TestWellPlannerMeasurementApis:
    def test_should_retrieve_well_planner_measured_wind_dataset(
        self, path: str, monitor_function_type: MonitorFunctionType
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1)

        start_datetime = datetime(
            year=well_planner.actual_start_date.year,
            month=well_planner.actual_start_date.month,
            day=well_planner.actual_start_date.day,
        )

        monitor_function = MonitorFunctionFactory(
            vessel=well_planner.asset.vessel,
            type=monitor_function_type,
        )

        MonitorFunctionValueFactory(monitor_function=monitor_function, value=1, date=start_datetime)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        expected_response = [
            {
                "date": datetime.combine(well_planner.actual_start_date, datetime.min.time()).isoformat() + 'Z',
                "value": 1.0,
            },
        ]

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self, path: str, monitor_function_type: MonitorFunctionType):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, deleted=True, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(
        self, path: str, monitor_function_type: MonitorFunctionType
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self, path: str, monitor_function_type: MonitorFunctionType):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, path: str, monitor_function_type: MonitorFunctionType):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerCompleteSummary:
    def test_should_retrieve_well_planner_complete_summary(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            improved_duration=2,
            external_energy_supply_enabled=False,
        )
        WellPlannerCompleteStepFactory(
            well_planner=well_planner,
            duration=1,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(baseline__asset=well_planner.asset, phase=planned_step.phase, mode=planned_step.mode)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_complete_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)
        expected_response = {
            "total_baseline": 0,
            "total_target": 0,
            "total_duration": 1.0,
        }

        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, deleted=True, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_complete_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_complete_summary',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_complete_summary',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_complete_summary',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    'view_name, step_id_name, current_step, step_factory_class',
    (
        (
            'wells:duplicate_well_planner_planned_step',
            'well_planner_planned_step_id',
            WellPlannerWizardStep.WELL_PLANNING,
            WellPlannerPlannedStepFactory,
        ),
        (
            'wells:duplicate_well_planner_complete_step',
            'well_planner_complete_step_id',
            WellPlannerWizardStep.WELL_REVIEWING,
            WellPlannerCompleteStepFactory,
        ),
        (
            'wells:duplicate_well_planner_complete_step',
            'well_planner_complete_step_id',
            WellPlannerWizardStep.WELL_REPORTING,
            WellPlannerCompleteStepFactory,
        ),
    ),
)
class TestDuplicateWellPlannerStepApi:
    def test_should_duplicate_well_planner_step(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        step_factory_class: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        step = step_factory_class(well_planner=well_planner)
        BaselineInputFactory(baseline=well_planner.baseline, phase=step.phase, mode=step.mode, season=step.season)
        ExternalEnergySupplyFactory(asset=well_planner.asset)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.post(url)

        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert response.status_code == 200

    def test_should_be_not_found_for_deleted_well_planner(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        step_factory_class: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        step = step_factory_class(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        step_factory_class: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        step = step_factory_class(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": 9999, step_id_name: step.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        step_factory_class: type[BaseWellPlannerStepFactory],
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        step = step_factory_class(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            view_name,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                step_id_name: step.pk,
            },
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        step_factory_class: type[BaseWellPlannerStepFactory],
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        step = step_factory_class(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    'view_name, step_id_name, current_step, StepFactory',
    (
        (
            'wells:move_well_planner_planned_step',
            'well_planner_planned_step_id',
            WellPlannerWizardStep.WELL_PLANNING,
            WellPlannerPlannedStepFactory,
        ),
        (
            'wells:move_well_planner_complete_step',
            'well_planner_complete_step_id',
            WellPlannerWizardStep.WELL_REVIEWING,
            WellPlannerCompleteStepFactory,
        ),
        (
            'wells:move_well_planner_complete_step',
            'well_planner_complete_step_id',
            WellPlannerWizardStep.WELL_REPORTING,
            WellPlannerCompleteStepFactory,
        ),
    ),
)
class TestMoveWellPlannerStepApi:
    def test_should_move_well_planner_step(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        first_step, second_step, third_step = StepFactory.create_batch(3, well_planner=well_planner)
        for step in [first_step, second_step, third_step]:
            BaselineInputFactory(baseline=well_planner.baseline, phase=step.phase, mode=step.mode, season=step.season)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                step_id_name: third_step.pk,
            },
        )
        response = api_client.put(url, data=dict(order=1))

        assert response.data == WellPlannerDetailsSerializer(well_planner).data
        assert response.status_code == 200

    def test_should_be_not_found_for_deleted_well_planner(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        step = StepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        step = StepFactory(well_planner__current_step=current_step)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant_user.tenant_id, "well_planner_id": 9999, step_id_name: step.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            view_name,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                step_id_name: 9999,
            },
        )
        response = api_client.put(url, data=dict(order=1))

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        step = StepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.put(url, data=dict(order=1))

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        view_name: str,
        step_id_name: str,
        current_step: WellPlannerWizardStep,
        StepFactory: type[BaseWellPlannerStepFactory],
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        step = StepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            view_name,
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk, step_id_name: step.pk},
        )
        response = api_client.put(url, data=dict(order=1))

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellReferenceMaterialApi:
    def test_should_retrieve_well_reference_material(self):
        tenant_user = TenantUserRelationFactory()
        reference_material = WellReferenceMaterialFactory(tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:wells_reference_material',
            kwargs={"tenant_id": tenant_user.tenant.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == WellReferenceMaterialSerializer(reference_material).data

    def test_should_be_not_found_for_non_existing_well_reference_material(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('wells:wells_reference_material', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        WellReferenceMaterialFactory(tenant=tenant)
        api_client = APIClient()

        url = reverse('wells:wells_reference_material', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        WellReferenceMaterialFactory(tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse('wells:wells_reference_material', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerPlannedStepCO2Api:
    def test_should_get_planned_step_co2(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            duration=7,
            improved_duration=5.5,
            external_energy_supply_enabled=False,
        )
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'rig': 0.0,
            'vessels': 0.0,
            'helicopters': 0.0,
            'external_energy_supply': 0.0,
            'cement': 0.0,
            'steel': 0.0,
            'emission_reduction_initiatives': [],
            'baseline': 0.0,
            'target': 0.0,
        }

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        planned_step = WellPlannerPlannedStepFactory()

        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant)
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": 9999,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            'wells:well_planner_planned_step_co2',
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                "well_planner_planned_step_id": planned_step.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,id_parameter_name,WellPlannerStepFactory,current_step",
    (
        (
            "wells:update_well_planner_planned_step_emission_reduction_initiatives",
            "well_planner_planned_step_id",
            WellPlannerPlannedStepFactory,
            WellPlannerWizardStep.WELL_PLANNING,
        ),
        (
            "wells:update_well_planner_complete_step_emission_reduction_initiatives",
            "well_planner_complete_step_id",
            WellPlannerCompleteStepFactory,
            WellPlannerWizardStep.WELL_REVIEWING,
        ),
        (
            "wells:update_well_planner_complete_step_emission_reduction_initiatives",
            "well_planner_complete_step_id",
            WellPlannerCompleteStepFactory,
            WellPlannerWizardStep.WELL_REPORTING,
        ),
    ),
)
class TestUpdateWellPlannerStepEmissionReductionInitiativeApi:
    def test_should_update_well_planner_step_emission_reduction_initiatives(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        well_planner_step = WellPlannerStepFactory(well_planner=well_planner)
        BaselineInputFactory(
            baseline=well_planner.baseline,
            phase=well_planner_step.phase,
            mode=well_planner_step.mode,
            season=well_planner_step.season,
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )
        well_planner_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)
        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )
        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: well_planner_step.pk,
            },
        )
        data = {
            "emission_reduction_initiatives": [
                emission_reduction_initiative.pk for emission_reduction_initiative in new_emission_reduction_initiatives
            ],
        }
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=data)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, current_step=current_step, deleted=True)
        well_planner_step = WellPlannerStepFactory(well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
                id_parameter_name: well_planner_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)
        well_planner_step = WellPlannerStepFactory(well_planner__current_step=current_step)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
                id_parameter_name: well_planner_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_step(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
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
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
        current_step: WellPlannerWizardStep,
    ):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        planned_step = WellPlannerStepFactory(well_planner=well_planner)
        api_client = APIClient()

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: planned_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(
        self,
        path: str,
        id_parameter_name: str,
        WellPlannerStepFactory: type[BaseWellPlannerStepFactory],
        current_step: WellPlannerWizardStep,
    ):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=current_step)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        url = reverse(
            path,
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
                id_parameter_name: planned_step.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestApproveWellPlannerCompleteHelicopterUses:
    def test_should_approve_complete_well_planner_complete_helicopter_uses(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        complete_helicopter_uses = CompleteHelicopterUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "complete_helicopter_uses": [
                complete_helicopter_uses[0].pk,
                complete_helicopter_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_helicopter_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "wells:approve_well_planner_complete_helicopter_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(
            url,
        )

        assert response.status_code == 404

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        complete_helicopter_uses = CompleteHelicopterUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "complete_helicopter_uses": [
                complete_helicopter_uses[0].pk,
                complete_helicopter_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_helicopter_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_uses = CompleteHelicopterUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()

        data = {
            "complete_helicopter_uses": [
                complete_helicopter_uses[0].pk,
                complete_helicopter_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_helicopter_uses",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_uses = CompleteHelicopterUseFactory.create_batch(2, well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        data = {
            "complete_helicopter_uses": [
                complete_helicopter_uses[0].pk,
                complete_helicopter_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_helicopter_uses",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestApproveWellPlannerCompleteVesselUses:
    def test_should_approve_complete_well_planner_complete_vessel_uses(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        complete_vessel_uses = CompleteVesselUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "complete_vessel_uses": [
                complete_vessel_uses[0].pk,
                complete_vessel_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_vessel_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "wells:approve_well_planner_complete_vessel_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(
            url,
        )

        assert response.status_code == 404

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        complete_vessel_uses = CompleteVesselUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {
            "complete_vessel_uses": [
                complete_vessel_uses[0].pk,
                complete_vessel_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_vessel_uses",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": 9999,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_uses = CompleteVesselUseFactory.create_batch(2, well_planner=well_planner)

        api_client = APIClient()

        data = {
            "complete_vessel_uses": [
                complete_vessel_uses[0].pk,
                complete_vessel_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_vessel_uses",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_uses = CompleteVesselUseFactory.create_batch(2, well_planner=well_planner)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        data = {
            "complete_vessel_uses": [
                complete_vessel_uses[0].pk,
                complete_vessel_uses[1].pk,
            ]
        }

        url = reverse(
            "wells:approve_well_planner_complete_vessel_uses",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateWellPlannerActualStartDateApi:
    def test_should_update_well_planner_actual_start_date(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant_user.tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING
        )
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"actual_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "wells:update_well_planner_actual_start_date",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 200
        assert response.data == WellPlannerDetailsSerializer(well_planner).data

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "wells:update_well_planner_actual_start_date",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        data = {"actual_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "wells:update_well_planner_actual_start_date",
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
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()

        data = {"actual_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "wells:update_well_planner_actual_start_date",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        api_client = APIClient()
        api_client.force_authenticate(user=user)

        data = {"actual_start_date": date(2022, 6, 1).isoformat()}

        url = reverse(
            "wells:update_well_planner_actual_start_date",
            kwargs={
                "tenant_id": tenant.pk,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.put(url, data=data)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerPhaseListApi:
    def test_should_retrieve_custom_well_planner_phase_list(self):
        well_planner = WellPlannerFactory()
        tenant_user = TenantUserRelationFactory(tenant=well_planner.asset.tenant)
        BaselineInputFactory(phase=CustomPhaseFactory(asset=well_planner.asset))
        transit_phase = CustomPhaseFactory(asset=well_planner.asset, phase__transit=True)
        custom_phase_with_phase = CustomPhaseFactory(asset=well_planner.asset, phase__transit=False)
        custom_phase_without_phase = CustomPhaseFactory(asset=well_planner.asset, phase=None)
        CustomPhaseFactory(asset=well_planner.asset, phase__transit=False)
        CustomPhaseFactory(asset=well_planner.asset, phase=None)
        CustomPhaseFactory()
        BaselineInputFactory(baseline=well_planner.baseline, phase=transit_phase)
        BaselineInputFactory(baseline=well_planner.baseline, phase=custom_phase_with_phase)
        BaselineInputFactory(baseline=well_planner.baseline, phase=custom_phase_without_phase)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'wells:custom_well_planner_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert (
            response.data
            == WellPlannerPhaseListSerializer(
                [transit_phase, custom_phase_with_phase, custom_phase_without_phase], many=True
            ).data
        )

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "wells:custom_well_planner_phase_list",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'wells:custom_well_planner_phase_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        url = reverse(
            'wells:custom_well_planner_phase_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'wells:custom_well_planner_phase_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerModeListApi:
    def test_should_retrieve_well_planner_mode_list(self):
        well_planner = WellPlannerFactory()
        tenant_user = TenantUserRelationFactory(tenant=well_planner.asset.tenant)
        BaselineInputFactory(mode=CustomModeFactory(asset=well_planner.asset))
        transit_mode = CustomModeFactory(asset=well_planner.asset, mode__transit=True)
        custom_mode_with_mode = CustomModeFactory(asset=well_planner.asset, mode__transit=False)
        custom_mode_without_mode = CustomModeFactory(asset=well_planner.asset, mode=None)
        CustomModeFactory(asset=well_planner.asset, mode__transit=False)
        CustomModeFactory(asset=well_planner.asset, mode=None)
        CustomModeFactory()
        BaselineInputFactory(baseline=well_planner.baseline, mode=transit_mode)
        BaselineInputFactory(baseline=well_planner.baseline, mode=custom_mode_with_mode)
        BaselineInputFactory(baseline=well_planner.baseline, mode=custom_mode_without_mode)

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'wells:well_planner_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert (
            response.data
            == WellPlannerModeListSerializer(
                [transit_mode, custom_mode_with_mode, custom_mode_without_mode], many=True
            ).data
        )

    def test_should_be_not_found_for_deleted_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)

        api_client = APIClient()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            "wells:well_planner_mode_list",
            kwargs={
                "tenant_id": tenant_user.tenant_id,
                "well_planner_id": well_planner.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_not_found_for_non_existing_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'wells:well_planner_mode_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)

        url = reverse(
            'wells:well_planner_mode_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)

        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'wells:well_planner_mode_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerEmissionReductionInitiativeListApi:
    def test_should_retrieve_emission_reduction_initiative_list(self):
        tenant_user = TenantUserRelationFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant_user.tenant, planned_start_date=date(2022, 7, 1))
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan, deployment_date=date(2022, 6, 1)
        )
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse(
            'wells:well_planner_emission_reduction_initiative_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 200
        assert (
            response.data == EmissionReductionInitiativeListSerializer([emission_reduction_initiative], many=True).data
        )

    def test_should_be_not_found_for_non_unknown_well_planner(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)
        well_planner = WellPlannerFactory()

        url = reverse(
            'wells:well_planner_emission_reduction_initiative_list',
            kwargs={"tenant_id": tenant_user.tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': "Not found."}

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        url = reverse(
            'wells:well_planner_emission_reduction_initiative_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        well_planner = WellPlannerFactory(asset__tenant=tenant)
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse(
            'wells:well_planner_emission_reduction_initiative_list',
            kwargs={"tenant_id": tenant.pk, "well_planner_id": well_planner.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestWellPlannerListApi:
    def test_should_retrieve_well_planner_list(self):
        tenant_user = TenantUserRelationFactory()
        first_well_planner, second_well_planner = WellPlannerFactory.create_batch(2, asset__tenant=tenant_user.tenant)
        WellPlannerFactory(asset__tenant=tenant_user.tenant, deleted=True)
        WellPlannerFactory()

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        url = reverse('wells:well_planner_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': WellPlannerListSerializer([second_well_planner, first_well_planner], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        tenant = TenantFactory()

        url = reverse('wells:well_planner_list', kwargs={"tenant_id": tenant.pk})
        api_client = APIClient()

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        tenant = TenantFactory()
        user = UserFactory()
        api_client = APIClient()
        api_client.force_authenticate(user)

        url = reverse('wells:well_planner_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
