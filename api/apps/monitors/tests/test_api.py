import datetime
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.monitors.choices import MonitorElementDatasetType
from apps.monitors.factories import (
    MonitorElementFactory,
    MonitorElementPhaseFactory,
    MonitorFactory,
    MonitorFunctionFactory,
    MonitorFunctionValueFactory,
)
from apps.monitors.models import Monitor
from apps.monitors.serializers import MonitorDetailsSerializer, MonitorElementDetailsSerializer, MonitorListSerializer
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestMonitorListApi:
    def test_should_retrieve_monitor_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('monitors:monitor_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)
        monitor = MonitorFactory(tenant=tenant_user.tenant)
        MonitorFactory(tenant=tenant_user.tenant, draft=True)
        MonitorFactory()

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': MonitorListSerializer([monitor], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('monitors:monitor_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('monitors:monitor_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestMonitorDetailsApi:
    def test_should_retrieve_monitor_details(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        monitor = MonitorFactory(
            tenant=tenant_user.tenant,
        )
        monitor_element = MonitorElementFactory(monitor=monitor)
        MonitorElementFactory(monitor=monitor, draft=True)
        url = reverse('monitors:monitor_details', kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        monitor = Monitor.objects.with_public_elements().get(pk=monitor.pk)
        assert response.data == MonitorDetailsSerializer(monitor).data
        assert response.data['elements'] == [MonitorElementDetailsSerializer(monitor_element).data]

    def test_should_be_not_found_for_non_existing_monitor(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        url = reverse('monitors:monitor_details', kwargs={"tenant_id": tenant_user.tenant_id, "monitor_id": 999})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': 'Not found.'}

    def test_should_be_not_found_for_draft_monitor(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        monitor = MonitorFactory(
            tenant=tenant_user.tenant,
            draft=True,
        )
        MonitorElementFactory.create_batch(2, monitor=monitor)
        url = reverse('monitors:monitor_details', kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404
        assert response.data == {'detail': 'Not found.'}

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        monitor = MonitorFactory()
        url = reverse('monitors:monitor_details', kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk})

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        monitor = MonitorFactory()
        user = UserFactory()
        url = reverse('monitors:monitor_details', kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk})
        api_client.force_authenticate(user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestMonitorElementDatasetListApi:
    @pytest.fixture()
    def setup(self):
        self.now = timezone.now().replace(minute=0, second=0)
        self.today = self.now.date()
        self.tenant_user = TenantUserRelationFactory()
        self.monitor = MonitorFactory(
            tenant=self.tenant_user.tenant,
            start_date=self.now - timedelta(days=2),
            end_date=self.now + timedelta(days=1),
        )
        MonitorElementFactory(monitor=self.monitor, draft=True)
        self.monitor_function = MonitorFunctionFactory()
        self.monitor_element = MonitorElementFactory(monitor=self.monitor, monitor_function=self.monitor_function)
        MonitorElementPhaseFactory(
            monitor_element=self.monitor_element,
            name='Transit',
            baseline=50,
            target=25,
            start_date=self.today - timedelta(days=2),
            end_date=self.today - timedelta(days=1),
        )
        MonitorElementPhaseFactory(
            name='Transit', baseline=250, target=225, start_date=self.today - timedelta(days=6), end_date=self.today
        )
        MonitorElementPhaseFactory(
            monitor_element=self.monitor_element,
            name='Drilling',
            baseline=70,
            target=30,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=1),
        )
        MonitorElementPhaseFactory(
            name='Drilling',
            baseline=170,
            target=130,
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=5),
        )

        MonitorFunctionValueFactory(monitor_function=self.monitor_function, date=self.now - timedelta(days=3))
        MonitorFunctionValueFactory(monitor_function=self.monitor_function, value=0, date=self.now - timedelta(days=2))
        MonitorFunctionValueFactory(monitor_function=self.monitor_function, value=50, date=self.now - timedelta(days=1))
        MonitorFunctionValueFactory(value=50, date=self.now - datetime.timedelta(hours=2))
        MonitorFunctionValueFactory(
            monitor_function=self.monitor_function, value=5, date=self.now - datetime.timedelta(hours=2)
        )
        MonitorFunctionValueFactory(
            monitor_function=self.monitor_function, value=25, date=self.now - datetime.timedelta(hours=1)
        )
        MonitorFunctionValueFactory(value=40, date=self.now)
        MonitorFunctionValueFactory(monitor_function=self.monitor_function, value=30, date=self.now)
        MonitorFunctionValueFactory(
            monitor_function=self.monitor_function, value=100, date=self.now + timedelta(days=1)
        )
        MonitorFunctionValueFactory(monitor_function=self.monitor_function, date=self.now + timedelta(days=2))

    @pytest.mark.freeze_time("2022-01-14 12:02:01")
    def test_should_retrieve_cumulative_dataset_list(self, setup: None):
        api_client = APIClient()
        url = (
            reverse(
                'monitors:monitor_element_dataset_list',
                kwargs={
                    "tenant_id": self.monitor.tenant_id,
                    "monitor_id": self.monitor.pk,
                    "element_id": self.monitor_element.pk,
                },
            )
            + f'?type={MonitorElementDatasetType.CUMULATIVE}'
        )
        api_client.force_authenticate(user=self.tenant_user.user)

        response = api_client.get(url)

        expected_response = [
            {
                'date': (self.today - timedelta(days=2)).isoformat(),
                'baseline': 50,
                'target': 25,
                'current': 0,
            },
            {
                'date': (self.today - timedelta(days=1)).isoformat(),
                'baseline': 100,
                'target': 50,
                'current': 50,
            },
            {
                'date': self.today.isoformat(),
                'baseline': 100,
                'target': 50,
                'current': 110,
            },
            {
                'date': (self.today + timedelta(days=1)).isoformat(),
                'baseline': 170,
                'target': 80,
                'current': None,
            },
        ]
        assert response.status_code == 200
        assert response.data == expected_response

    @pytest.mark.freeze_time("2022-01-14 12:02:01")
    def test_should_retrieve_daily_dataset_list(self, setup: None):
        api_client = APIClient()
        url = (
            reverse(
                'monitors:monitor_element_dataset_list',
                kwargs={
                    "tenant_id": self.monitor.tenant_id,
                    "monitor_id": self.monitor.pk,
                    "element_id": self.monitor_element.pk,
                },
            )
            + f'?type={MonitorElementDatasetType.DAILY}'
        )
        api_client.force_authenticate(user=self.tenant_user.user)

        response = api_client.get(url)

        expected_response = [
            {
                'date': (self.today - timedelta(days=2)).isoformat(),
                'baseline': 50,
                'target': 25,
                'current': 0,
            },
            {
                'date': (self.today - timedelta(days=1)).isoformat(),
                'baseline': 50,
                'target': 25,
                'current': 50,
            },
            {
                'date': self.today.isoformat(),
                'baseline': None,
                'target': None,
                'current': 60,
            },
            {
                'date': (self.today + timedelta(days=1)).isoformat(),
                'baseline': 70,
                'target': 30,
                'current': None,
            },
        ]
        assert response.status_code == 200
        assert response.data == expected_response

    def test_should_be_not_found_for_draft_monitor(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        monitor = MonitorFactory(
            tenant=tenant_user.tenant,
            draft=True,
        )
        monitor_element = MonitorElementFactory(monitor=monitor)

        url = reverse(
            'monitors:monitor_element_dataset_list',
            kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk, "element_id": monitor_element.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404

    def test_should_be_not_found_for_draft_monitor_element(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        monitor = MonitorFactory(
            tenant=tenant_user.tenant,
        )
        monitor_element = MonitorElementFactory(monitor=monitor, draft=True)

        url = reverse(
            'monitors:monitor_element_dataset_list',
            kwargs={"tenant_id": monitor.tenant_id, "monitor_id": monitor.pk, "element_id": monitor_element.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 404

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        monitor_element = MonitorElementFactory()
        url = reverse(
            'monitors:monitor_element_dataset_list',
            kwargs={
                "tenant_id": monitor_element.monitor.tenant_id,
                "monitor_id": monitor_element.monitor_id,
                "element_id": monitor_element.pk,
            },
        )

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        monitor_element = MonitorElementFactory()
        tenant_user = TenantUserRelationFactory()
        url = reverse(
            'monitors:monitor_element_dataset_list',
            kwargs={
                "tenant_id": monitor_element.monitor.tenant_id,
                "monitor_id": monitor_element.monitor_id,
                "element_id": monitor_element.pk,
            },
        )
        api_client.force_authenticate(tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
