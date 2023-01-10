import pytest

from apps.tenants.factories import TenantFactory, TenantUserRelationFactory, UserFactory


@pytest.mark.django_db
class TestUserFactory:
    def test_factory(self):
        UserFactory()


@pytest.mark.django_db
class TestTenantFactory:
    def test_factory(self):
        TenantFactory()


@pytest.mark.django_db
class TestTenantUserRelationFactory:
    def test_factory(self):
        TenantUserRelationFactory()
