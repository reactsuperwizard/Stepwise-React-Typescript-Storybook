import datetime

import pytest
from django.utils import timezone

from apps.core.factories import SessionRequestFactory
from apps.wells.factories import CustomWellFactory
from apps.wells.filters import CustomWellListFilter
from apps.wells.models import CustomWell


@pytest.mark.django_db
class TestCustomWellListLatestFilter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.latest = CustomWellFactory(created_at=timezone.now())
        CustomWellFactory(created_at=timezone.now() - datetime.timedelta(days=3))

        self.qs = CustomWell.objects.all()
        self.request = SessionRequestFactory()

    def test_no_latest_filter(self):
        assert CustomWellListFilter(queryset=self.qs, request=self.request, data=dict()).qs.count() == 2

    def test_filter_by_latest_true(self):
        assert (
            CustomWellListFilter(queryset=self.qs, request=self.request, data=dict(latest=True)).qs.get() == self.latest
        )

    def test_filter_by_latest_false(self):
        assert CustomWellListFilter(queryset=self.qs, request=self.request, data=dict(latest=False)).qs.count() == 2


@pytest.mark.django_db
class TestCustomWellListDraftFilter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.draft = CustomWellFactory(draft=True)
        self.public = CustomWellFactory(draft=False)

        self.qs = CustomWell.objects.all()
        self.request = SessionRequestFactory()

    def test_no_draft_filter(self):
        assert CustomWellListFilter(queryset=self.qs, request=self.request, data=dict()).qs.count() == 2

    def test_filter_by_draft_true(self):
        assert (
            CustomWellListFilter(queryset=self.qs, request=self.request, data=dict(draft=True)).qs.get() == self.draft
        )

    def test_filter_by_draft_false(self):
        assert (
            CustomWellListFilter(queryset=self.qs, request=self.request, data=dict(draft=False)).qs.get() == self.public
        )
