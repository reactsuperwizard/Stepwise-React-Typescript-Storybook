import datetime

import pytest
from django.utils import timezone

from apps.core.factories import SessionRequestFactory
from apps.rigs.factories import CustomJackupRigFactory
from apps.rigs.filters import CustomRigListFilter
from apps.rigs.models import CustomJackupRig


@pytest.mark.django_db
class TestCustomRigListLatestFilter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.latest = CustomJackupRigFactory(created_at=timezone.now())
        CustomJackupRigFactory(created_at=timezone.now() - datetime.timedelta(days=3))

        self.qs = CustomJackupRig.objects.all()
        self.request = SessionRequestFactory()

    def test_no_latest_filter(self):
        assert CustomRigListFilter(queryset=self.qs, request=self.request, data=dict()).qs.count() == 2

    def test_filter_by_latest_true(self):
        assert (
            CustomRigListFilter(queryset=self.qs, request=self.request, data=dict(latest=True)).qs.get() == self.latest
        )

    def test_filter_by_latest_false(self):
        assert CustomRigListFilter(queryset=self.qs, request=self.request, data=dict(latest=False)).qs.count() == 2


@pytest.mark.django_db
class TestCustomRigListDraftFilter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.draft = CustomJackupRigFactory(draft=True)
        self.public = CustomJackupRigFactory(draft=False)

        self.qs = CustomJackupRig.objects.all()
        self.request = SessionRequestFactory()

    def test_no_draft_filter(self):
        assert CustomRigListFilter(queryset=self.qs, request=self.request, data=dict()).qs.count() == 2

    def test_filter_by_draft_true(self):
        assert CustomRigListFilter(queryset=self.qs, request=self.request, data=dict(draft=True)).qs.get() == self.draft

    def test_filter_by_draft_false(self):
        assert (
            CustomRigListFilter(queryset=self.qs, request=self.request, data=dict(draft=False)).qs.get() == self.public
        )
