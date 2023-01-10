import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.emps.factories import ConceptEMPElementFactory
from apps.emps.serializers import ConceptEMPElementSerializer
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestConceptEMPElementListApi:
    def test_should_retrieve_concept_emp_element_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        concept_emp_element = ConceptEMPElementFactory()

        url = reverse('emps:concept_emp_element_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == ConceptEMPElementSerializer([concept_emp_element], many=True).data

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        user = UserFactory()
        tenant = TenantFactory()

        url = reverse('emps:concept_emp_element_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user=user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()

        url = reverse('emps:concept_emp_element_list', kwargs={"tenant_id": tenant.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}
