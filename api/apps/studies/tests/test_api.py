import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.projects.factories import PlanFactory, ProjectFactory
from apps.rigs.factories import CustomDrillshipFactory, CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import RigType
from apps.studies.factories import (
    JACKUP_STUDY_METRIC_KEYS,
    SEMI_STUDY_METRIC_KEYS,
    StudyElementDrillshipRelationFactory,
    StudyElementFactory,
    StudyElementJackupRigRelationFactory,
    StudyElementSemiRigRelationFactory,
    StudyMetricFactory,
)
from apps.studies.models import StudyElement
from apps.studies.serializers import (
    StudyElementListSerializer,
    StudyElementSerializer,
    StudyMetricSerializer,
    SwappedStudyElementsSerializer,
)
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestStudyElementDetailsApi:
    @pytest.mark.parametrize(
        "metric_key",
        set(JACKUP_STUDY_METRIC_KEYS) & set(SEMI_STUDY_METRIC_KEYS),
    )
    def test_should_retrieve_study_element(self, metric_key: str):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        study_element = StudyElementFactory(project=project, order=0, metric__key=metric_key)

        semi_rig_relation = StudyElementSemiRigRelationFactory(study_element=study_element)
        StudyElementSemiRigRelationFactory()
        jackup_rig_relation = StudyElementJackupRigRelationFactory(study_element=study_element)
        StudyElementJackupRigRelationFactory()
        drillship_rig_relation = StudyElementDrillshipRelationFactory(study_element=study_element)
        StudyElementDrillshipRelationFactory()

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == StudyElementSerializer(study_element).data
        assert response.data['rigs'] == [
            StudyElementSerializer.StudyElementSemiRigSerializer(semi_rig_relation).data,
            StudyElementSerializer.StudyElementJackupRigSerializer(jackup_rig_relation).data,
            StudyElementSerializer.StudyElementDrillshipSerializer(drillship_rig_relation).data,
        ]

    def test_should_be_not_found_for_study_element_from_different_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        study_element = StudyElementFactory(project__tenant=tenant_user.tenant)

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_not_found_for_non_existing_project(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        study_element = StudyElementFactory(order=0, project__tenant=tenant_user.tenant)

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": 999, "element_id": study_element.pk},
        )
        api_client.force_authenticate(tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_not_found_for_non_existing_study_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": project.pk, "element_id": 999},
        )
        api_client.force_authenticate(tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        study_element = StudyElementFactory(project__tenant=tenant)

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant.pk, "project_id": study_element.project.pk, "element_id": study_element.pk},
        )
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        study_element = StudyElementFactory(project__tenant=tenant)

        url = reverse(
            'studies:study_element_details',
            kwargs={"tenant_id": tenant.pk, "project_id": study_element.project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestStudyElementListApi:
    def test_should_retrieve_study_element_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        first_study_element = StudyElementFactory(project=project, order=1)
        second_study_element = StudyElementFactory(project=project, order=0)

        url = reverse(
            'studies:study_element_list', kwargs={"tenant_id": tenant_user.tenant.pk, "project_id": project.pk}
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == StudyElementListSerializer([second_study_element, first_study_element], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        url = reverse('studies:study_element_list', kwargs={"tenant_id": tenant.pk, "project_id": project.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)
        url = reverse('studies:study_element_list', kwargs={"tenant_id": tenant.pk, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestStudyMetricListApi:
    def test_should_retrieve_study_metric_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        study_metric = StudyMetricFactory()
        url = reverse('studies:study_metric_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == [StudyMetricSerializer(study_metric).data]

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('studies:study_metric_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('studies:study_metric_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestDeleteStudyElementApi:
    def test_should_delete_study_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        study_element = StudyElementFactory(project=project)
        StudyElementSemiRigRelationFactory(study_element=study_element)
        StudyElementJackupRigRelationFactory(study_element=study_element)
        StudyElementDrillshipRelationFactory(study_element=study_element)

        url = reverse(
            'studies:delete_study_element',
            kwargs={"tenant_id": tenant_user.tenant_id, "project_id": project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)
        response = api_client.delete(url)

        assert response.status_code == 204
        assert response.data is None
        assert StudyElement.objects.filter(pk=study_element.pk).exists() is False

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        study_element = StudyElementFactory(project=project)
        url = reverse(
            'studies:delete_study_element',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )

        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)
        study_element = StudyElementFactory(project=project)
        url = reverse(
            'studies:delete_study_element',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )

        api_client.force_authenticate(user=user)
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestCreateStudyElementApi:
    def test_should_create_study_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        jackup_rig = CustomJackupRigFactory(tenant=tenant_user.tenant, project=project)
        semi_rig = CustomSemiRigFactory(tenant=tenant_user.tenant, project=project)
        drillship = CustomDrillshipFactory(tenant=tenant_user.tenant, project=project)
        plan = PlanFactory(project=project)
        metric = StudyMetricFactory()
        data = {
            "title": "Test chart",
            "plan": plan.pk,
            "metric": metric.key,
            "rigs": [
                {'id': semi_rig.pk, 'type': RigType.SEMI},
                {'id': jackup_rig.pk, 'type': RigType.JACKUP},
                {'id': drillship.pk, 'type': RigType.DRILLSHIP},
            ],
        }
        url = reverse(
            'studies:create_study_element', kwargs={"tenant_id": tenant_user.tenant_id, "project_id": project.pk}
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=data, format='json')

        assert response.status_code == 201
        study_element = StudyElement.objects.get()
        assert response.data == StudyElementListSerializer(study_element).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        url = reverse('studies:create_study_element', kwargs={"tenant_id": tenant.pk, "project_id": project.pk})

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        user = UserFactory()
        url = reverse('studies:create_study_element', kwargs={"tenant_id": tenant.pk, "project_id": project.pk})
        api_client.force_authenticate(user)

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUpdateStudyElementApi:
    def test_should_update_study_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(
            tenant=tenant_user.tenant,
        )
        first_jackup_rig, second_jackup_rig = CustomJackupRigFactory.create_batch(
            2, tenant=tenant_user.tenant, project=project
        )
        first_semi_rig, second_semi_rig = CustomSemiRigFactory.create_batch(
            2, tenant=tenant_user.tenant, project=project
        )
        first_drillship, second_drillship = CustomDrillshipFactory.create_batch(
            2, tenant=tenant_user.tenant, project=project
        )
        plan = PlanFactory(project=project)
        metric = StudyMetricFactory()
        study_element = StudyElementFactory(project=project)
        StudyElementSemiRigRelationFactory(study_element=study_element, rig=first_semi_rig)
        StudyElementJackupRigRelationFactory(study_element=study_element, rig=first_jackup_rig)
        StudyElementDrillshipRelationFactory(study_element=study_element, rig=first_drillship)
        data = {
            "title": "Updated chart",
            "plan": plan.pk,
            "metric": metric.key,
            "rigs": [
                {'id': second_jackup_rig.pk, 'type': RigType.JACKUP},
                {'id': second_semi_rig.pk, 'type': RigType.SEMI},
                {'id': second_drillship.pk, 'type': RigType.DRILLSHIP},
            ],
        }
        url = reverse(
            'studies:update_study_element',
            kwargs={"tenant_id": tenant_user.tenant_id, "project_id": project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.put(url, data=data, format='json')

        assert response.status_code == 200
        study_element.refresh_from_db()
        assert response.data == StudyElementListSerializer(study_element).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        study_element = StudyElementFactory(project=project)
        url = reverse(
            'studies:update_study_element',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        study_element = StudyElementFactory(project=project)
        user = UserFactory()
        url = reverse(
            'studies:update_study_element',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk, "element_id": study_element.pk},
        )
        api_client.force_authenticate(user)

        response = api_client.put(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestSwapStudyElementsApi:
    def test_should_swap_study_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        project = ProjectFactory(tenant=tenant_user.tenant)
        first_study_element, second_study_element = StudyElementFactory.create_batch(2, project=project)
        data = {
            "first_element": first_study_element.pk,
            "second_element": second_study_element.pk,
        }
        url = reverse(
            'studies:swap_study_elements',
            kwargs={"tenant_id": tenant_user.tenant_id, "project_id": project.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url, data=data)

        assert response.status_code == 200
        first_study_element.refresh_from_db()
        second_study_element.refresh_from_db()
        assert (
            response.data
            == SwappedStudyElementsSerializer(
                {"first_element": first_study_element, "second_element": second_study_element}
            ).data
        )

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        url = reverse(
            'studies:swap_study_elements',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk},
        )

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        project = ProjectFactory(tenant=tenant)
        user = UserFactory()
        url = reverse(
            'studies:swap_study_elements',
            kwargs={"tenant_id": tenant.pk, "project_id": project.pk},
        )
        api_client.force_authenticate(user)

        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
