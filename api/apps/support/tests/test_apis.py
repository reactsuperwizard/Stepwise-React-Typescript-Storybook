import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.support.factories import FaqElementFactory, FaqFactory
from apps.support.serializers import FaqSerializer
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory


@pytest.mark.django_db
class TestFaqApi:
    def test_should_retrieve_faqs(self):
        tenant_user = TenantUserRelationFactory()
        api_client = APIClient()
        faq_element_1 = FaqElementFactory()
        FaqElementFactory(faq=faq_element_1.faq, draft=True)
        FaqElementFactory(draft=True)
        FaqElementFactory(faq__draft=True)
        FaqFactory()

        url = reverse('support:faq', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 200

        assert len(response.data) == 1
        assert response.data[0]["title"] == faq_element_1.faq.title
        assert response.data[0]["elements"] == FaqSerializer.FaqElementSerializer([faq_element_1], many=True).data

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()

        url = reverse('support:faq', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        tenant = TenantFactory()

        url = reverse('support:faq', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(tenant_user.user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
