from datetime import timedelta

import factory.fuzzy
from django.conf import settings
from django.utils import timezone

from apps.tenants.models import TenantUserRelation, UserRole

USER_PASSWORD = "password"


class TenantFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("company")
    subdomain = factory.Sequence(lambda n: f'test{n}.example.com')

    class Meta:
        model = "tenants.Tenant"
        django_get_or_create = ('subdomain',)


class UserFactory(factory.django.DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Sequence(lambda n: f"user{n}@example.com")
    email = factory.LazyAttribute(lambda o: o.username)
    role = UserRole.ADMIN  # TODO: introduce other roles
    company = factory.SubFactory(TenantFactory)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(USER_PASSWORD)

    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('email',)


class TenantUserRelationFactory(factory.django.DjangoModelFactory):
    tenant = factory.SubFactory(TenantFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.fuzzy.FuzzyChoice(choices=TenantUserRelation.TenantUserRole.values)

    class Meta:
        model = "tenants.TenantUserRelation"
        django_get_or_create = (
            'tenant',
            'user',
        )


class TenantInvitationFactory(factory.django.DjangoModelFactory):
    tenant = factory.SubFactory(TenantFactory)
    email = factory.Sequence(lambda n: f'invitation-test-{n}@example.com')
    token = factory.Sequence(lambda n: f'signup-token-{n}')
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=settings.SIGNUP_TOKEN_EXPIRE_AFTER_DAYS))
    is_active = True

    class Meta:
        model = "tenants.TenantInvitation"
        django_get_or_create = ('tenant', 'email', 'is_active')
