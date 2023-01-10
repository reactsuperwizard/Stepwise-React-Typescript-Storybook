import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.notifications.factories import NotificationFactory
from apps.notifications.serializers import NotificationListSerializer
from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestNotificationListApi:
    def test_should_retrieve_notification_list(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        notification = NotificationFactory(tenant_user=tenant_user)
        NotificationFactory()
        url = reverse('notifications:notification_list', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
            'next': None,
            'previous': None,
            'results': NotificationListSerializer([notification], many=True).data,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('notifications:notification_list', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('notifications:notification_list', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestReadNotificationsApi:
    def test_should_read_notifications(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        NotificationFactory(tenant_user=tenant_user)
        url = reverse('notifications:read_notifications', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url)

        assert response.status_code == 204

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('notifications:read_notifications', kwargs={"tenant_id": tenant.pk})
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('notifications:read_notifications', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestUnreadNotificationsApi:
    def test_should_retrieve_number_of_unread_notifications(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        NotificationFactory(tenant_user=tenant_user)
        NotificationFactory(tenant_user=tenant_user, read=True)
        NotificationFactory()
        url = reverse('notifications:unread_notifications', kwargs={"tenant_id": tenant_user.tenant.pk})
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data == {
            'count': 1,
        }

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        url = reverse('notifications:unread_notifications', kwargs={"tenant_id": tenant.pk})
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        url = reverse('notifications:unread_notifications', kwargs={"tenant_id": tenant.pk})
        api_client.force_authenticate(user)
        response = api_client.get(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}


@pytest.mark.django_db
class TestReadNotificationApi:
    def test_should_read_notification(self):
        api_client = APIClient()
        tenant_user = TenantUserRelationFactory()
        notification = NotificationFactory(tenant_user=tenant_user)
        url = reverse(
            'notifications:read_notification',
            kwargs={"tenant_id": tenant_user.tenant.pk, "notification_id": notification.pk},
        )
        api_client.force_authenticate(user=tenant_user.user)

        response = api_client.post(url)

        assert response.status_code == 204

    def test_should_be_forbidden_for_anonymous_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        notification = NotificationFactory(tenant_user__tenant=tenant)
        url = reverse(
            'notifications:read_notification', kwargs={"tenant_id": tenant.pk, "notification_id": notification.pk}
        )
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'Authentication credentials were not provided.'}

    def test_should_be_forbidden_for_non_tenant_user(self):
        api_client = APIClient()
        tenant = TenantFactory()
        user = UserFactory()
        notification = NotificationFactory(tenant_user__tenant=tenant)
        url = reverse(
            'notifications:read_notification', kwargs={"tenant_id": tenant.pk, "notification_id": notification.pk}
        )
        api_client.force_authenticate(user)
        response = api_client.post(url)

        assert response.status_code == 403
        assert response.data == {"detail": 'You do not have permission to perform this action.'}
