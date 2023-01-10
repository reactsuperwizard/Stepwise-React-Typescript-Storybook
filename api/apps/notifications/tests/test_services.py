import pytest

from apps.notifications.factories import NotificationFactory
from apps.notifications.services import read_notification, read_notifications
from apps.tenants.factories import TenantUserRelationFactory


@pytest.mark.django_db
def test_read_notifications():
    tenant_user = TenantUserRelationFactory()
    NotificationFactory()
    NotificationFactory(tenant_user=tenant_user, read=True)
    notification = NotificationFactory(tenant_user=tenant_user)

    assert notification.read is False

    num_read = read_notifications(user=tenant_user.user, tenant=tenant_user.tenant)

    assert num_read == 1

    notification.refresh_from_db()
    assert notification.read is True


@pytest.mark.django_db
class TestReadNotification:
    def test_read_read_notification(self):
        tenant_user = TenantUserRelationFactory()
        notification = NotificationFactory(tenant_user=tenant_user, read=True)

        assert notification.read is True

        assert read_notification(user=tenant_user.user, notification=notification) is False

        notification.refresh_from_db()
        assert notification.read is True

    def test_read_unread_notification(self):
        tenant_user = TenantUserRelationFactory()
        notification = NotificationFactory(tenant_user=tenant_user)

        assert notification.read is False

        assert read_notification(user=tenant_user.user, notification=notification) is True

        notification.refresh_from_db()
        assert notification.read is True
