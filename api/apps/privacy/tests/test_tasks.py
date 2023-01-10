from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock

import pytest
from celery import states
from django.utils import timezone

from apps.privacy.factories import DeleteAccountRequestFactory
from apps.privacy.tasks import execute_delete_account_request, execute_delete_account_requests


@pytest.mark.django_db
class TestExecuteDeleteAccountRequests:
    @mock.patch.object(execute_delete_account_request, "delay")
    def test_should_execute_delete_account_requests(self, mock_execute_delete_account_request: MagicMock):
        delete_account_request = DeleteAccountRequestFactory(execute_at=timezone.now() - timedelta(days=2))
        DeleteAccountRequestFactory(is_active=False, execute_at=timezone.now() - timedelta(days=2))
        DeleteAccountRequestFactory()

        result = execute_delete_account_requests.apply()

        assert result.get() is None
        assert result.state == states.SUCCESS

        mock_execute_delete_account_request.assert_called_once_with(delete_account_request.pk)


@pytest.mark.django_db
class TestExecuteDeleteAccountRequest:
    def test_should_execute_delete_account_request(self):
        delete_account_request = DeleteAccountRequestFactory(execute_at=timezone.now() - timedelta(days=2))

        result = execute_delete_account_request.apply(args=(delete_account_request.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS
