from django.utils import timezone

from apps.app.celery import app
from apps.privacy.models import DeleteAccountRequest
from apps.privacy.services import delete_account


@app.task
def execute_delete_account_requests() -> None:
    """
    Execute all pending delete account requests
    """
    delete_account_requests = DeleteAccountRequest.objects.filter(is_active=True, execute_at__lte=timezone.now())

    for request in delete_account_requests:
        execute_delete_account_request.delay(request.pk)


@app.task
def execute_delete_account_request(delete_account_request_id: int) -> None:
    """
    Execute a single delete account request
    """
    delete_account_request = DeleteAccountRequest.objects.get(pk=delete_account_request_id)
    delete_account(delete_account_request)
