from unittest import mock

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.privacy.factories import PrivacyPolicyConsentFactory, PrivacyPolicyFactory
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory


@pytest.mark.django_db
class TestPrivacyPolicyDetailsApi:
    def test_should_retrieve_policy_details(self, api_client: APIClient):
        policy = PrivacyPolicyFactory()

        url = reverse('privacy:policy_details', kwargs={"policy_id": policy.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "id": policy.pk,
            "text": policy.text,
            "title": policy.title,
        }

    def test_should_be_not_found_for_non_existing_policy(self, api_client: APIClient):
        url = reverse('privacy:policy_details', kwargs={"policy_id": 99999})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}


@pytest.mark.django_db
class TestPrivacyPolicyLatestApi:
    def test_should_retrieve_active_policy_details(self, api_client: APIClient):
        active_policy = PrivacyPolicyFactory()
        PrivacyPolicyFactory(is_active=False)

        url = reverse('privacy:policy_latest')
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "id": active_policy.pk,
            "text": active_policy.text,
            "title": active_policy.title,
        }

    def test_should_be_not_found_for_non_existing_active_policy(self, api_client: APIClient):
        PrivacyPolicyFactory(is_active=False)
        url = reverse('privacy:policy_latest')
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}


@pytest.mark.django_db
class TestPrivacyPolicyLatestAcceptApi:
    def test_should_accept_policy(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)
        PrivacyPolicyFactory()

        url = reverse('privacy:policy_latest_accept', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 204
        assert response.data is None

    def test_should_be_forbidden_for_unauthenticated_user(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('privacy:policy_latest_accept', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_not_found_for_non_existing_policy(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('privacy:policy_latest_accept', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}


@pytest.mark.django_db
class TestPrivacyPolicyConsentListApi:
    def test_should_retrieve_consents_for_logged_in_user(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        consent = PrivacyPolicyConsentFactory(user=tenant_user.user)
        api_client.force_authenticate(user=tenant_user.user)
        PrivacyPolicyConsentFactory(policy=consent.policy)

        url = reverse('privacy:consent_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == [
            {
                "id": consent.pk,
                "title": consent.policy.title,
                "text": consent.policy.text,
                "created_at": mock.ANY,
                "revoked_at": None,
            }
        ]

    def test_should_be_forbidden_for_unauthenticated_user(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('privacy:consent_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}


@pytest.mark.django_db
class TestDeleteAccountApi:
    def test_should_delete_account(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_login(user=tenant_user.user)
        url = reverse('privacy:delete_account', kwargs={"tenant_id": tenant_user.tenant.pk})

        assert '_auth_user_id' in api_client.session

        response = api_client.delete(url)

        assert '_auth_user_id' not in api_client.session
        assert response.status_code == 204
        assert response.data is None

    def test_should_be_forbidden_for_unauthenticated_user(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('privacy:delete_account', kwargs={"tenant_id": tenant.pk})
        response = api_client.delete(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}


@pytest.mark.django_db
class TestPrivacyPolicyConsentLatestApi:
    def test_should_retrieve_the_latest_consent_for_logged_in_user(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        _, latest_consent = PrivacyPolicyConsentFactory.create_batch(2, user=tenant_user.user, policy__is_active=False)
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('privacy:consent_latest', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            "id": latest_consent.pk,
            "title": latest_consent.policy.title,
            "text": latest_consent.policy.text,
            "created_at": mock.ANY,
            "revoked_at": None,
        }

    def test_should_be_forbidden_for_unauthenticated_user(self, api_client: APIClient):
        tenant = TenantFactory()
        url = reverse('privacy:consent_latest', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_not_found_for_non_existing_consent(self, api_client: APIClient):
        tenant_user = TenantUserRelationFactory()
        api_client.force_authenticate(user=tenant_user.user)

        url = reverse('privacy:consent_latest', kwargs={"tenant_id": tenant_user.tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {"detail": 'Not found.'}
