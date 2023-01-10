import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.dashboard import DashboardRoutes
from apps.monitors.factories import MonitorFactory
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db(transaction=True)
class TestSearchApi:
    def test_should_retrieve_search_results(self, clear_haystack):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('search:search', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        monitor = MonitorFactory(tenant=tenant_user.tenant, name='Test monitor')
        # for some reason monitor is not indexed without extra save
        monitor.save()
        MonitorFactory(name='Test monitor')

        response = api_client.get(url, dict(query="monitor"))

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': f'monitors.monitor.{monitor.pk}',
                    'url': DashboardRoutes.monitor.format(monitorId=monitor.pk),
                    'type': 'Monitor',
                    'name': monitor.name,
                }
            ],
        }

    def test_should_retrieve_paginated_search_results(self, clear_haystack):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('search:search', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        first, second, third = MonitorFactory.create_batch(3, tenant=tenant_user.tenant, name='Test monitor')

        response = api_client.get(url, dict(query="monitor", page_size=2, page=2))

        assert response.status_code == 200
        assert response.data['next'] is None
        assert response.data['previous'] is not None
        assert response.data['results'] == [
            {
                'id': f'monitors.monitor.{third.pk}',
                'url': DashboardRoutes.monitor.format(monitorId=third.pk),
                'type': 'Monitor',
                'name': third.name,
            }
        ]

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('search:search', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('search:search', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
