import logging

from apps.notifications.models import Notification
from apps.tenants.models import Tenant, User

logger = logging.getLogger(__name__)


def read_notifications(*, user: User, tenant: Tenant) -> int:
    logger.info(f'User(pk={user.pk}) is reading all notifications')
    num_read = Notification.objects.filter(
        tenant_user__tenant=tenant,
        tenant_user__user=user,
        read=False,
    ).update(read=True)
    logger.info(f'{num_read} notifications marked as read')
    return num_read


def read_notification(*, user: User, notification: Notification) -> bool:
    logger.info(f'User(pk={user.pk}) is reading Notification(pk={notification.pk})')
    if notification.read:
        logger.info('Notification is already read')
        return False

    notification.read = True
    notification.save()
    logger.info('Notification marked as read')
    return True
