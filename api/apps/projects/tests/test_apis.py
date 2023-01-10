import datetime

import pytest
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from apps.emps.factories import ConceptEMPElementFactory, CustomEMPElementFactory, EMPFactory
from apps.emps.models import ConceptEMPElement
from apps.emps.serializers import EMPSerializer
from apps.emps.services import EMPData
from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.projects.models import Plan, Project
from apps.projects.serializers import (
    ElementListSerializer,
    PlanDetailsSerializer,
    PlanListSerializer,
    ProjectDetailsSerializer,
    ProjectListSerializer,
)
from apps.rigs.factories import (
    AnyCustomRigFactory,
    CustomDrillshipFactory,
    CustomJackupRigFactory,
    CustomSemiRigFactory,
)
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig, RigType
from apps.rigs.serializers import CustomRigListSerializer
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory
from apps.tenants.models import Tenant, TenantUserRelation
from apps.wells.factories import CustomWellFactory, WellPlannerFactory
from apps.wells.models import CustomWell
from apps.wells.serializers import CustomWellListSerializer


@pytest.mark.django_db
class TestProjectListApi:
    values = 'id', 'description', 'name', 'created_at', 'updated_at'

    @pytest.fixture
    def tenant(self) -> Tenant:
        return TenantFactory()

    @pytest.fixture
    def tenant_user(self, tenant: Tenant) -> TenantUserRelation:
        return TenantUserRelationFactory(tenant=tenant)

    @pytest.fixture
    def first_project(self, tenant: Tenant) -> Project:
        return ProjectFactory(
            name='First Project', tenant=tenant, created_at=timezone.now() - datetime.timedelta(days=1)
        )

    @pytest.fixture
    def second_project(self, tenant: Tenant) -> Project:
        return ProjectFactory(name='Second Project', tenant=tenant)

    @pytest.fixture(autouse=True)
    def setup_project_list(self, first_project: Project, second_project: Project, tenant_user: TenantUserRelation):
        ProjectFactory()
        WellPlannerFactory()

    def serialize_project(self, project_id: int):
        return Project.objects.filter(pk=project_id).values(*self.values).get()

    def test_should_retrieve_project_list(
        self, first_project: Project, second_project: Project, tenant_user: TenantUserRelation
    ):
        url = reverse('projects:project_list', kwargs={"tenant_id": tenant_user.tenant.pk})

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 2,
            'next': None,
            'previous': None,
            'results': ProjectListSerializer(
                [
                    self.serialize_project(second_project.id),
                    self.serialize_project(first_project.id),
                ],
                many=True,
            ).data,
        }

    @pytest.mark.parametrize(
        'ordering,results',
        (
            ('-created_at', ['Second Project', 'First Project']),
            ('created_at', ['First Project', 'Second Project']),
            ('name', ['First Project', 'Second Project']),
            ('-name', ['Second Project', 'First Project']),
        ),
    )
    def test_should_order_project_list(self, ordering: str, results: list[str], tenant_user: TenantUserRelation):
        url = reverse('projects:project_list', kwargs={"tenant_id": tenant_user.tenant.pk}) + f'?ordering={ordering}'

        api_client = APIClient()
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert list(map(lambda result: result['name'], response.data['results'])) == results

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('projects:project_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('projects:project_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectDetailsApi:
    def test_should_retrieve_project_details(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(
            tenant=tenant_user.tenant,
        )
        CustomSemiRigFactory(tenant=tenant_user.tenant, project=project)
        CustomJackupRigFactory(tenant=tenant_user.tenant, project=project)
        CustomWellFactory(tenant=tenant_user.tenant, project=project)
        url = reverse('projects:project_details', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        project = Project.objects.prefetch_related(
            Prefetch('semi_rigs', queryset=CustomSemiRig.objects.with_type()),
            Prefetch('jackup_rigs', queryset=CustomJackupRig.objects.with_type()),
        ).get(pk=project.pk)
        assert response.data == ProjectDetailsSerializer(project).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        url = reverse('projects:project_details', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        user = UserFactory()
        url = reverse('projects:project_details', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateProjectApi:
    def test_should_create_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        data = {
            "name": "Test project",
            "description": "Project description",
            "tugs_day_rate": 300.0,
            "tugs_avg_move_fuel_consumption": 22.0,
            "tugs_avg_transit_fuel_consumption": 11.0,
            "tugs_move_speed": 2.5,
            "tugs_transit_speed": 12.0,
            "ahv_no_used": 5,
            "ahv_no_days_per_location": 7,
            "ahv_avg_fuel_consumption": 3.0,
            "ahv_day_rate": 1000.0,
            "psv_calls_per_week": 2,
            "psv_types": "PS 213, PSV 153",
            "psv_day_rate": 7000.0,
            "psv_avg_fuel_transit_consumption": 12.0,
            "psv_avg_fuel_dp_consumption": 5.5,
            "psv_speed": 12.0,
            "psv_loading_time": 0.25,
            "psv_fuel_price": 2000.0,
            "helicopter_no_flights_per_week": 7,
            "helicopter_types": "UH-60 Black Hawk",
            "helicopter_avg_fuel_consumption": 3.5,
            "helicopter_rate_per_trip": 200.0,
            "helicopter_fuel_price": 333,
            "helicopter_cruise_speed": 120.0,
            "marine_diesel_oil_price": 3000,
            "co2_tax": 60,
            "nox_tax": 88,
            "fuel_total_price": 3456,
            "fuel_density": 3.6,
            "co2_emission_per_tonne_fuel": 3.0,
            "co2_emission_per_m3_fuel": 4.0,
        }
        url = reverse('projects:create_project', kwargs={"tenant_id": tenant_user.tenant_id})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=data)

        assert response.status_code == 201
        project = Project.objects.get()
        assert response.data == {**ProjectDetailsSerializer(project).data, **data}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('projects:create_project', kwargs={"tenant_id": tenant.pk})

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('projects:create_project', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateProjectApi:
    def test_should_update_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        data = {
            "name": "Updated project",
            "description": "Updated project description",
            "tugs_day_rate": 400.0,
            "tugs_avg_move_fuel_consumption": 25.0,
            "tugs_avg_transit_fuel_consumption": 11.1,
            "tugs_move_speed": 3.5,
            "tugs_transit_speed": 13.5,
            "ahv_no_used": 6,
            "ahv_no_days_per_location": 8,
            "ahv_avg_fuel_consumption": 4.0,
            "ahv_day_rate": 2000.0,
            "psv_calls_per_week": 3,
            "psv_types": "PS 213",
            "psv_day_rate": 8000.0,
            "psv_avg_fuel_transit_consumption": 13.0,
            "psv_avg_fuel_dp_consumption": 6.5,
            "psv_speed": 13.0,
            "psv_fuel_price": 2000.0,
            "psv_loading_time": 0.35,
            "helicopter_no_flights_per_week": 8,
            "helicopter_types": "Boeing AH-64 Apache",
            "helicopter_avg_fuel_consumption": 4.5,
            "helicopter_rate_per_trip": 300.0,
            "helicopter_fuel_price": 433,
            "helicopter_cruise_speed": 120.0,
            "marine_diesel_oil_price": 4000,
            "co2_tax": 70,
            "nox_tax": 98,
            "fuel_total_price": 4456,
            "fuel_density": 3.6,
            "co2_emission_per_tonne_fuel": 4.0,
            "co2_emission_per_m3_fuel": 4.0,
        }
        url = reverse('projects:update_project', kwargs={"tenant_id": tenant_user.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=data)

        assert response.status_code == 200
        project.refresh_from_db()
        assert response.data == {**ProjectDetailsSerializer(project).data, **data}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        url = reverse('projects:update_project', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        user = UserFactory()
        url = reverse('projects:update_project', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectRigListApi:
    @pytest.fixture
    def setup_project_rig_list(self):
        self.api_client = APIClient()
        self.tenant_user = TenantUserRelationFactory()
        self.project = ProjectFactory(
            tenant=self.tenant_user.tenant,
        )
        CustomSemiRigFactory(tenant=self.tenant_user.tenant)
        self.semi_rig = CustomSemiRigFactory(tenant=self.tenant_user.tenant, project=self.project, name="Semi Rig")
        CustomSemiRigFactory()
        CustomJackupRigFactory(tenant=self.tenant_user.tenant)
        self.jackup_rig = CustomJackupRigFactory(
            tenant=self.tenant_user.tenant, project=self.project, name="Jackup Rig"
        )
        CustomJackupRigFactory()
        CustomDrillshipFactory(tenant=self.tenant_user.tenant)
        self.drillship = CustomDrillshipFactory(
            tenant=self.tenant_user.tenant, project=self.project, name="Drillship rig"
        )
        CustomDrillshipFactory()
        CustomWellFactory(tenant=self.tenant_user.tenant, project=self.project)

    def test_should_retrieve_project_rig_list(self, setup_project_rig_list: None):
        url = reverse(
            'projects:project_rig_list', kwargs={"tenant_id": self.project.tenant_id, "project_id": self.project.pk}
        )
        self.api_client.force_authenticate(user=self.tenant_user.user)

        response = self.api_client.get(url)

        values = ('id', 'name', 'type', 'created_at', 'updated_at', 'draft', 'project_id', 'emp_id')
        assert response.status_code == 200
        assert (
            response.data
            == CustomRigListSerializer(
                [
                    CustomDrillship.objects.with_type().filter(pk=self.drillship.pk).values(*values).first(),
                    CustomJackupRig.objects.with_type().filter(pk=self.jackup_rig.pk).values(*values).first(),
                    CustomSemiRig.objects.with_type().filter(pk=self.semi_rig.pk).values(*values).first(),
                ],
                many=True,
            ).data
        )

    @pytest.mark.parametrize(
        'ordering,results',
        (
            ('-created_at', ['Drillship rig', 'Jackup Rig', 'Semi Rig']),
            ('created_at', ['Semi Rig', 'Jackup Rig', 'Drillship rig']),
            ('name', ['Drillship rig', 'Jackup Rig', 'Semi Rig']),
            ('-name', ['Semi Rig', 'Jackup Rig', 'Drillship rig']),
        ),
    )
    def test_should_order_project_rig_list(self, ordering: str, results: list[str], setup_project_rig_list: None):
        url = (
            reverse(
                'projects:project_rig_list', kwargs={"tenant_id": self.project.tenant_id, "project_id": self.project.pk}
            )
            + f'?ordering={ordering}'
        )
        self.api_client.force_authenticate(user=self.tenant_user.user)

        response = self.api_client.get(url)

        assert response.status_code == 200

        assert list(map(lambda result: result['name'], response.data)) == results

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        url = reverse('projects:project_rig_list', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        user = UserFactory()
        url = reverse('projects:project_rig_list', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectWellListApi:
    def test_should_retrieve_project_well_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        CustomWellFactory()
        project = ProjectFactory(
            tenant=tenant_user.tenant,
        )
        well = CustomWellFactory(tenant=tenant_user.tenant, project=project)
        url = reverse('projects:project_well_list', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == CustomWellListSerializer([well], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        url = reverse('projects:project_well_list', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        user = UserFactory()
        url = reverse('projects:project_well_list', kwargs={"tenant_id": project.tenant_id, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectPlanListApi:
    def test_should_retrieve_project_plan_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory(project__tenant=tenant_user.tenant)
        PlanWellRelationFactory(plan=plan)
        PlanFactory()

        url = reverse(
            'projects:project_plan_list', kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk}
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == PlanListSerializer([plan], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        plan = PlanFactory()
        url = reverse(
            'projects:project_plan_list', kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk}
        )

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        plan = PlanFactory()
        user = UserFactory()
        url = reverse(
            'projects:project_plan_list', kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk}
        )
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectPlanDetailsApi:
    def test_should_retrieve_project_plan_details(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory(project__tenant=tenant_user.tenant)
        PlanWellRelationFactory(plan=plan)

        url = reverse(
            'projects:project_plan_details',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == PlanDetailsSerializer(plan).data

    def test_should_be_not_found_for_non_existing_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory(project__tenant=tenant_user.tenant)
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'projects:project_plan_details',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": 999, "plan_id": plan.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_not_found_for_non_existing_plan(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'projects:project_plan_details',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "plan_id": 999},
        )
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        plan = PlanFactory()
        url = reverse(
            'projects:project_plan_details',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        plan = PlanFactory()
        user = UserFactory()
        url = reverse(
            'projects:project_plan_details',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateProjectPlanApi:
    def test_should_create_project_plan(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        well = CustomWellFactory(tenant=tenant_user.tenant)
        rig = CustomJackupRigFactory(project=project, tenant=tenant_user.tenant)
        project.wells.add(well)

        plan_data = {
            "name": "Plan name",
            "description": "Plan description",
            "block_name": "Plan block name",
            "distance_from_tug_base_to_previous_well": 100.0,
            "reference_rig": {"id": rig.pk, "type": RigType.JACKUP},
            "wells": [
                {
                    "id": well.pk,
                    "distance_from_previous_location": 10,
                    "distance_to_helicopter_base": 20,
                    "distance_to_psv_base": 30,
                    "distance_to_ahv_base": 40,
                    "distance_to_tug_base": 50.5,
                    "jackup_positioning_time": 1.2,
                    "semi_positioning_time": 1.3,
                    "operational_time": 20,
                }
            ],
        }

        url = reverse(
            'projects:create_project_plan',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=plan_data, format='json')

        assert response.status_code == 201
        plan = Plan.objects.get()
        assert response.data == PlanDetailsSerializer(plan).data

    def test_should_be_not_found_for_non_existing_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse(
            'projects:create_project_plan',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": 999},
        )
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()
        url = reverse(
            'projects:create_project_plan',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()
        url = reverse(
            'projects:create_project_plan',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )

        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateProjectPlanApi:
    def test_should_update_project_plan(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        jackup_rig = CustomJackupRigFactory(project=project, tenant=tenant_user.tenant)
        semi_rig = CustomSemiRigFactory(project=project, tenant=tenant_user.tenant, dp=True)
        plan = PlanFactory(project=project, reference_operation_jackup=jackup_rig)
        plan_well = PlanWellRelationFactory(plan=plan)
        PlanWellRelationFactory(plan=plan)

        well = CustomWellFactory(tenant=tenant_user.tenant)
        plan.project.wells.add(well)

        plan_data = {
            "name": "Updated plan name",
            "description": "Updated plan description",
            "block_name": "Updated plan block name",
            "distance_from_tug_base_to_previous_well": 200.0,
            "reference_rig": {"id": semi_rig.pk, "type": RigType.SEMI},
            "wells": [
                {
                    "id": plan_well.well.pk,
                    "distance_from_previous_location": 1,
                    "distance_to_helicopter_base": 2,
                    "distance_to_psv_base": 3,
                    "distance_to_ahv_base": 4,
                    "distance_to_tug_base": 5.5,
                    "jackup_positioning_time": 2.6,
                    "semi_positioning_time": 2.7,
                    "operational_time": 20,
                },
                {
                    "id": well.pk,
                    "distance_from_previous_location": 9,
                    "distance_to_helicopter_base": 10,
                    "distance_to_psv_base": 11,
                    "distance_to_ahv_base": 12,
                    "distance_to_tug_base": 13.5,
                    "jackup_positioning_time": 1.14,
                    "semi_positioning_time": 1.15,
                    "operational_time": 21,
                },
            ],
        }

        url = reverse(
            'projects:update_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.put(url, data=plan_data, format='json')

        assert response.status_code == 200
        plan.refresh_from_db()
        assert response.data == PlanDetailsSerializer(plan).data

    def test_should_be_not_found_for_non_existing_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory(project__tenant=tenant_user.tenant)

        url = reverse(
            'projects:update_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": 999, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_not_found_for_non_existing_plan(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            'projects:update_project_plan',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "plan_id": 999},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.put(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        plan = PlanFactory()

        url = reverse(
            'projects:update_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory()

        url = reverse(
            'projects:update_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteProjectPlanApi:
    def test_should_delete_project_plan(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory(project__tenant=tenant_user.tenant)
        PlanWellRelationFactory(plan=plan)

        url = reverse(
            'projects:delete_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None
        assert Plan.objects.filter(pk=plan.pk).first() is None

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        plan = PlanFactory()

        url = reverse(
            'projects:delete_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        plan = PlanFactory()

        url = reverse(
            'projects:delete_project_plan',
            kwargs={"tenant_id": plan.project.tenant.pk, "project_id": plan.project.pk, "plan_id": plan.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestProjectRigEmpDetailsApi:
    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_retrieve_emp_details(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, project=project)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == EMPSerializer(rig.emp).data

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_non_existing_emp(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(emp=None, project=project)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_non_existing_project(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(emp=None)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": tenant_user.tenant.pk,
                "project_id": 999,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_non_project_rig(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(emp=None)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type",
        (
            RigType.JACKUP,
            RigType.SEMI,
            RigType.DRILLSHIP,
        ),
    )
    def test_should_be_not_found_for_non_existing_rig(self, rig_type: str):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": 999,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_anonymous_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_non_tenant_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        project = ProjectFactory()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:project_rig_emp_details",
            kwargs={
                "tenant_id": project.tenant.pk,
                "project_id": project.pk,
                "rig_type": rig_type.lower(),
                "rig_id": rig.pk,
            },
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateProjectRigEMPApi:
    @pytest.fixture
    def concept_emp_element(self) -> ConceptEMPElement:
        return ConceptEMPElementFactory()

    @pytest.fixture
    def emp_data(self, concept_emp_element: ConceptEMPElement) -> dict:
        return dict(
            name="EMP name",
            description="EMP description",
            api_description="EMP api description",
            start_date=datetime.date.today().isoformat(),
            end_date=datetime.date.today().isoformat(),
            total_rig_baseline_average=10.0,
            total_rig_target_average=20.0,
            elements=[
                dict(
                    concept_id=concept_emp_element.pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
            ],
        )

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_create_emp(self, rig_type: str, emp_data: EMPData, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, emp=None, project=project)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=emp_data, format='json')

        assert response.status_code == 201
        rig.refresh_from_db()
        assert response.data == EMPSerializer(rig.emp).data

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_non_existing_project(
        self, rig_type: str, emp_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant, emp=None)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": rig.tenant.pk, "project_id": 999, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=emp_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type",
        (
            RigType.JACKUP,
            RigType.SEMI,
            RigType.DRILLSHIP,
        ),
    )
    def test_should_be_not_found_for_non_existing_rig(self, rig_type: str, emp_data: EMPData):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": 999},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=emp_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_rig_from_another_project(
        self, rig_type: str, emp_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, emp=None)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=emp_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_anonymous_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, emp=None, project=project)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_non_tenant_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, emp=None, project=project)

        url = reverse(
            "projects:create_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateProjectRigEMPApi:
    @pytest.fixture
    def emp_update_data(self) -> dict:
        emp = EMPFactory()
        custom_emp_element = CustomEMPElementFactory(emp=emp)  # Should be udpated
        CustomEMPElementFactory(emp=emp)  # Should be deleted

        return dict(
            name="Updated EMP name",
            description="Updated EMP description",
            api_description="Updated EMP api description",
            start_date=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
            end_date=(datetime.date.today() + datetime.timedelta(days=2)).isoformat(),
            total_rig_baseline_average=10.0,
            total_rig_target_average=20.0,
            elements=[
                dict(
                    id=custom_emp_element.pk,
                    concept_id=custom_emp_element.concept_emp_element.pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
                dict(
                    concept_id=ConceptEMPElementFactory().pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
            ],
        )

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_update_emp(self, rig_type: str, emp_update_data: EMPData, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, project=project)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=emp_update_data, format='json')

        assert response.status_code == 200
        rig.refresh_from_db()
        assert response.data == EMPSerializer(rig.emp).data

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_non_existing_project(
        self, rig_type: str, emp_update_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        rig = RigFactory(tenant=tenant_user.tenant)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": rig.tenant.pk, "project_id": 999, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=emp_update_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type",
        (
            RigType.JACKUP,
            RigType.SEMI,
            RigType.DRILLSHIP,
        ),
    )
    def test_should_be_not_found_for_non_existing_rig(self, rig_type: str, emp_update_data: EMPData):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": 999},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=emp_update_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_not_found_for_rig_from_another_project(
        self, rig_type: str, emp_update_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=emp_update_data, format='json')

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_anonymous_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    @pytest.mark.parametrize(
        "rig_type, RigFactory",
        (
            (RigType.JACKUP, CustomJackupRigFactory),
            (RigType.SEMI, CustomSemiRigFactory),
            (RigType.DRILLSHIP, CustomDrillshipFactory),
        ),
    )
    def test_should_be_forbidden_for_non_tenant_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:update_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rig_type, RigFactory",
    (
        (RigType.JACKUP, CustomJackupRigFactory),
        (RigType.SEMI, CustomSemiRigFactory),
        (RigType.DRILLSHIP, CustomDrillshipFactory),
    ),
)
class TestDeleteProjectRigEMPApi:
    def test_should_delete_emp(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, project=project)

        url = reverse(
            "projects:delete_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_not_found_for_rig_without_emp(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        rig = RigFactory(tenant=tenant_user.tenant, emp=None, project=project)

        url = reverse(
            "projects:delete_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {"detail": "Not found."}

    def test_should_be_forbidden_for_non_anonymous_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:delete_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self, rig_type: str, RigFactory: AnyCustomRigFactory):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()
        rig = RigFactory(tenant=project.tenant, project=project)

        url = reverse(
            "projects:delete_project_rig_emp",
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk, "rig_type": rig_type, "rig_id": rig.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestElementListApi:
    def test_should_retrieve_element_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('projects:element_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        semi_rig = CustomSemiRigFactory(tenant=tenant_user.tenant, project=None)
        CustomSemiRigFactory()
        CustomJackupRigFactory()
        CustomDrillshipFactory()
        well = CustomWellFactory(tenant=tenant_user.tenant, project=None)
        CustomWellFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        jackup_rig = CustomJackupRigFactory(tenant=tenant_user.tenant, project=project)
        drillship = CustomDrillshipFactory(tenant=tenant_user.tenant, project=project)

        response = api_client.get(url)

        values = ('id', 'name', 'element_type', 'created_at', 'updated_at', 'project')
        assert response.status_code == 200
        assert response.data == {
            'count': 4,
            'next': None,
            'previous': None,
            'results': ElementListSerializer(
                [
                    CustomDrillship.objects.with_element_type().filter(pk=drillship.pk).values(*values).get(),
                    CustomJackupRig.objects.with_element_type().filter(pk=jackup_rig.pk).values(*values).get(),
                    CustomWell.objects.with_element_type().filter(pk=well.pk).values(*values).get(),
                    CustomSemiRig.objects.with_element_type().filter(pk=semi_rig.pk).values(*values).get(),
                ],
                many=True,
            ).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('projects:element_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('projects:element_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteProjectApi:
    def test_should_delete_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            'projects:delete_project',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None
        assert Project.objects.filter(pk=project.pk).exists() is False

    def test_should_be_forbidden_from_removing_others_projects(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()

        url = reverse(
            'projects:delete_project',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": project.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 404
        assert response.data == {'detail': ErrorDetail(string='Not found.', code='not_found')}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        project = ProjectFactory()

        url = reverse(
            'projects:delete_project',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory()

        url = reverse(
            'projects:delete_project',
            kwargs={"tenant_id": project.tenant.pk, "project_id": project.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
